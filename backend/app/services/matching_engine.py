"""Spatial-Temporal Matching and Harmonisation Engine (Stages D, E, F & G)."""

import math
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from pyproj import Geod
from shapely import Point
from shapely.strtree import STRtree

from backend.app.schemas.datasets import RowQualityStatus, SensorType
from backend.app.schemas.observations import StandardizedObservationSchema
from backend.app.schemas.runs import (
    AmbiguityPolicy,
    CandidateDecision,
    HarmonisedRecord,
    HarmonisedRecordProvenance,
    InputDatasetIds,
    MatchCandidateRecord,
    MatchingParameters,
    MatchStatus,
    ProcessingRunCounts,
    ProcessingRunRates,
    ProcessingRunSummary,
    ReviewStatus,
    RunStatus,
    TimeWindowRule,
)


class HarmonisationEngineResult(BaseModel):
    """Structured six-part output of the Harmonisation Engine (Stage G)."""

    match_candidates: List[MatchCandidateRecord] = Field(
        description="All evaluated candidate links within thresholds"
    )
    harmonised_records: List[HarmonisedRecord] = Field(
        description="All harmonised observation records (matched, unmatched, ambiguous)"
    )
    unmatched_modis_records: List[HarmonisedRecord] = Field(
        description="Preserved MODIS detections without matching VIIRS candidates"
    )
    unmatched_viirs_records: List[HarmonisedRecord] = Field(
        description="Preserved VIIRS detections without matching MODIS candidates"
    )
    ambiguous_records: List[HarmonisedRecord] = Field(
        description="Detections involved in multiple candidate pairings"
    )
    summary_report: ProcessingRunSummary = Field(
        description="Complete execution summary, counts, scientific rates, and metrics"
    )

    model_config = ConfigDict(from_attributes=True)


class MatchingEngineService:
    """
    Core scientific matching engine implementing Stages D, E, F, and G:
    - Stage D: STRtree spatial indexing, antimeridian handling, and WGS84 geodesic calculation.
    - Stage E: Transparent uncalibrated spatial-temporal ranking score.
    - Stage F: Ambiguity policy resolution (retain_ambiguous, one_to_one_deterministic, many_to_many).
    - Stage G: Preservation of unmatched detections, separate sensor FRPs, and 6-part result.
    """

    # WGS 84 Ellipsoid geodesic computer
    _geod = Geod(ellps="WGS84")
    SCORE_DEFINITION = "Uncalibrated linear spatial-temporal proximity ranking score; not a probability"

    @classmethod
    def parse_datetime(cls, dt_str: str) -> Optional[datetime]:
        """Safely parse timezone-aware UTC datetime."""
        if not dt_str:
            return None
        clean = dt_str.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(clean)
        except Exception:
            return None

    @classmethod
    def compute_geodesic_distance(
        cls, lon1: float, lat1: float, lon2: float, lat2: float
    ) -> float:
        """
        Compute geodesic distance in metres on WGS 84 ellipsoid using pyproj.Geod.
        Handles dateline / antimeridian wrapping accurately.
        """
        # Geod.inv expects (lon1, lat1, lon2, lat2)
        _, _, distance_m = cls._geod.inv(lon1, lat1, lon2, lat2)
        return float(distance_m)

    @classmethod
    def haversine_distance_meters(
        cls, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Alias for compute_geodesic_distance."""
        return cls.compute_geodesic_distance(lon1, lat1, lon2, lat2)

    @classmethod
    def execute_matching_run(
        cls,
        run_id: str,
        modis_observations: List[StandardizedObservationSchema],
        viirs_observations: List[StandardizedObservationSchema],
        parameters: MatchingParameters,
        **kwargs,
    ):
        """Legacy helper returning (harmonised_records, match_candidates, summary_report)."""
        res = cls.run_harmonisation(run_id, modis_observations, viirs_observations, parameters, **kwargs)
        return res.harmonised_records, res.match_candidates, res.summary_report

    @classmethod
    def calculate_ranking_score(
        cls,
        spatial_distance_m: float,
        time_difference_s: float,
        max_distance_meters: float,
        max_time_difference_seconds: float,
        w_d: float = 0.5,
        w_t: float = 0.5,
    ) -> float:
        """
        Stage E: Candidate ranking score calculation:
        d_norm = spatial_distance_m / max_distance_meters
        t_norm = time_difference_s / max_time_difference_seconds
        score = round(1.0 - (w_d * d_norm + w_t * t_norm), 6)
        """
        d_norm = (
            min(spatial_distance_m / max_distance_meters, 1.0)
            if max_distance_meters > 0.0
            else 0.0
        )
        t_norm = (
            min(time_difference_s / max_time_difference_seconds, 1.0)
            if max_time_difference_seconds > 0.0
            else 0.0
        )
        score = 1.0 - (w_d * d_norm + w_t * t_norm)
        return round(float(np.clip(score, 0.0, 1.0)), 6)

    @classmethod
    def filter_eligible_observations(
        cls,
        observations: List[StandardizedObservationSchema],
        parameters: MatchingParameters,
    ) -> List[StandardizedObservationSchema]:
        """
        Filter observations for Stage D matching:
        - Exclude rejected rows.
        - Exclude warning rows if include_warnings is False.
        - Apply sensor-specific confidence filters.
        """
        q_filters = parameters.quality_filters
        eligible = []

        for obs in observations:
            # Exclude rejected rows always
            if obs.row_quality_status == RowQualityStatus.REJECTED:
                continue

            # Exclude warning rows if configured
            if (
                obs.row_quality_status == RowQualityStatus.WARNING
                and not q_filters.include_warnings
            ):
                continue

            # MODIS confidence filter
            if (
                obs.source_sensor == SensorType.MODIS
                and q_filters.min_modis_confidence is not None
            ):
                if obs.confidence_raw is not None:
                    try:
                        conf_val = float(obs.confidence_raw)
                        if conf_val < q_filters.min_modis_confidence:
                            continue
                    except (ValueError, TypeError):
                        pass

            # VIIRS confidence filter
            if (
                obs.source_sensor == SensorType.VIIRS
                and q_filters.allowed_viirs_confidence_levels
            ):
                if obs.confidence_raw is not None:
                    conf_str = str(obs.confidence_raw).strip().lower()
                    allowed_lower = [
                        str(x).strip().lower()
                        for x in q_filters.allowed_viirs_confidence_levels
                    ]
                    if conf_str not in allowed_lower:
                        continue

            eligible.append(obs)

        return eligible

    @classmethod
    def run_harmonisation(
        cls,
        run_id: str,
        modis_observations: List[StandardizedObservationSchema],
        viirs_observations: List[StandardizedObservationSchema],
        parameters: MatchingParameters,
        modis_input_count: int = 0,
        viirs_input_count: int = 0,
        modis_warning_count: int = 0,
        viirs_warning_count: int = 0,
        modis_rejected_count: int = 0,
        viirs_rejected_count: int = 0,
    ) -> HarmonisationEngineResult:
        """
        Execute full spatial-temporal matching pipeline: Stages D through G.
        """
        start_wall_time = time.time()
        started_at_iso = datetime.now().isoformat()

        # Step 1: Quality & Eligibility Filtering
        m_eligible = cls.filter_eligible_observations(modis_observations, parameters)
        v_eligible = cls.filter_eligible_observations(viirs_observations, parameters)

        # Parse timestamps for all eligible observations
        m_dts: Dict[str, datetime] = {}
        for m in m_eligible:
            dt = cls.parse_datetime(m.observation_time_utc)
            if dt:
                m_dts[m.observation_id] = dt

        v_dts: Dict[str, datetime] = {}
        for v in v_eligible:
            dt = cls.parse_datetime(v.observation_time_utc)
            if dt:
                v_dts[v.observation_id] = dt

        # Drop any observation whose timestamp failed parsing
        m_eligible = [m for m in m_eligible if m.observation_id in m_dts]
        v_eligible = [v for v in v_eligible if v.observation_id in v_dts]

        modis_by_id = {m.observation_id: m for m in m_eligible}
        viirs_by_id = {v.observation_id: v for v in v_eligible}

        max_dist = parameters.max_distance_meters
        max_time = parameters.max_time_difference_seconds
        rule = parameters.time_window_rule
        policy = parameters.ambiguity_policy
        method_version = parameters.matching_method_version

        w_d = parameters.score_weights.spatial_weight if parameters.score_weights else 0.5
        w_t = (
            parameters.score_weights.temporal_weight
            if parameters.score_weights
            else 0.5
        )

        # Step 2: Stage D Spatial Indexing & Candidate Generation
        candidates: List[MatchCandidateRecord] = []
        modis_candidates_map: Dict[str, List[MatchCandidateRecord]] = {
            m.observation_id: [] for m in m_eligible
        }
        viirs_candidates_map: Dict[str, List[MatchCandidateRecord]] = {
            v.observation_id: [] for v in v_eligible
        }

        if m_eligible and v_eligible:
            # Build STRtree spatial index on VIIRS points
            # 1 degree latitude ~ 111,320m. Buffer query box with generous margin
            lat_buffer_deg = (max_dist / 111320.0) + 0.02

            v_geoms = [Point(v.longitude, v.latitude) for v in v_eligible]
            tree = STRtree(v_geoms)

            # Check if any points are near the antimeridian (longitude near +-180)
            has_antimeridian_points = any(
                abs(abs(v.longitude) - 180.0) < 2.0 for v in v_eligible
            ) or any(abs(abs(m.longitude) - 180.0) < 2.0 for m in m_eligible)

            if has_antimeridian_points:
                # Build wrapped 0-360 tree for antimeridian safety
                v_geoms_wrapped = [
                    Point((v.longitude + 360.0) % 360.0, v.latitude)
                    for v in v_eligible
                ]
                tree_wrapped = STRtree(v_geoms_wrapped)
            else:
                tree_wrapped = None

            for m in m_eligible:
                m_id = m.observation_id
                m_dt = m_dts[m_id]
                m_lon, m_lat = m.longitude, m.latitude

                # Approximate degree buffer for longitude based on latitude
                cos_lat = max(math.cos(math.radians(m_lat)), 0.05)
                lon_buffer_deg = (max_dist / (111320.0 * cos_lat)) + 0.02

                # Query standard bounding box
                query_geom = Point(m_lon, m_lat).buffer(max(lat_buffer_deg, lon_buffer_deg))
                candidate_v_indices = set(tree.query(query_geom))

                # If near antimeridian, query wrapped tree as well
                if tree_wrapped is not None and abs(abs(m_lon) - 180.0) < 2.0:
                    m_lon_wrapped = (m_lon + 360.0) % 360.0
                    query_geom_wrapped = Point(m_lon_wrapped, m_lat).buffer(
                        max(lat_buffer_deg, lon_buffer_deg)
                    )
                    wrapped_indices = tree_wrapped.query(query_geom_wrapped)
                    candidate_v_indices.update(wrapped_indices)

                for v_idx in candidate_v_indices:
                    v = v_eligible[v_idx]
                    v_id = v.observation_id
                    v_dt = v_dts[v_id]

                    # Temporal rule check
                    signed_dt = (v_dt - m_dt).total_seconds()
                    abs_dt = abs(signed_dt)

                    if rule == TimeWindowRule.ABSOLUTE:
                        if abs_dt > max_time:
                            continue
                    elif rule == TimeWindowRule.DIRECTIONAL:
                        if not (0.0 <= signed_dt <= max_time):
                            continue

                    # Exact WGS 84 geodesic distance check
                    dist_m = cls.compute_geodesic_distance(
                        m_lon, m_lat, v.longitude, v.latitude
                    )
                    if dist_m > max_dist:
                        continue

                    # Stage E: Candidate ranking score
                    score = cls.calculate_ranking_score(
                        dist_m, abs_dt, max_dist, max_time, w_d, w_t
                    )

                    cand = MatchCandidateRecord(
                        id=f"cand-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        modis_observation_id=m_id,
                        viirs_observation_id=v_id,
                        spatial_distance_m=round(dist_m, 2),
                        time_difference_s=round(abs_dt, 2),
                        score=score,
                        decision=CandidateDecision.PENDING,
                        decision_reason="Generated within spatial and temporal thresholds",
                    )
                    candidates.append(cand)
                    modis_candidates_map[m_id].append(cand)
                    viirs_candidates_map[v_id].append(cand)

        # Step 3: Stage F Ambiguity Resolution
        harmonised_records: List[HarmonisedRecord] = []
        matched_modis_ids: Set[str] = set()
        matched_viirs_ids: Set[str] = set()
        ambiguous_modis_ids: Set[str] = set()
        ambiguous_viirs_ids: Set[str] = set()

        if policy == AmbiguityPolicy.RETAIN_AMBIGUOUS:
            for m_id, m_cands in modis_candidates_map.items():
                deg_m = len(m_cands)
                if deg_m == 1:
                    cand = m_cands[0]
                    v_id = cand.viirs_observation_id
                    deg_v = len(viirs_candidates_map[v_id])
                    if deg_v == 1:
                        # 1:1 mutual candidate -> Matched
                        cand.decision = CandidateDecision.ACCEPTED
                        cand.decision_reason = "unique_1_to_1_candidate_within_threshold"
                        matched_modis_ids.add(m_id)
                        matched_viirs_ids.add(v_id)

                        m_obs = modis_by_id[m_id]
                        v_obs = viirs_by_id[v_id]
                        rec = HarmonisedRecord(
                            harmonisation_id=f"harm-{uuid.uuid4().hex[:12]}",
                            run_id=run_id,
                            modis_observation_id=m_id,
                            viirs_observation_id=v_id,
                            match_status=MatchStatus.MATCHED,
                            spatial_distance_m=cand.spatial_distance_m,
                            time_difference_s=cand.time_difference_s,
                            matching_method_version=method_version,
                            matching_parameters=parameters,
                            match_score=cand.score,
                            review_status=ReviewStatus.UNREVIEWED,
                            provenance=HarmonisedRecordProvenance(
                                modis_source_record_id=m_obs.source_record_id,
                                viirs_source_record_id=v_obs.source_record_id,
                                modis_product_version=m_obs.product_version,
                                viirs_product_version=v_obs.product_version,
                                score_formula_note=cls.SCORE_DEFINITION,
                                candidate_count=1,
                                decision_reason="unique_1_to_1_candidate_within_threshold",
                            ),
                            modis_observation=m_obs,
                            viirs_observation=v_obs,
                            candidate_links=[cand],
                        )
                        harmonised_records.append(rec)
                    else:
                        ambiguous_modis_ids.add(m_id)
                        ambiguous_viirs_ids.add(v_id)
                elif deg_m > 1:
                    ambiguous_modis_ids.add(m_id)
                    for c in m_cands:
                        ambiguous_viirs_ids.add(c.viirs_observation_id)

            # Record ambiguous records (preserve all candidate links in provenance)
            for m_id in ambiguous_modis_ids:
                m_cands = modis_candidates_map[m_id]
                for c in m_cands:
                    c.decision = CandidateDecision.AMBIGUOUS
                    c.decision_reason = f"ambiguous_cluster_modis_deg_{len(m_cands)}_viirs_deg_{len(viirs_candidates_map[c.viirs_observation_id])}"

                m_obs = modis_by_id[m_id]
                first_v = (
                    viirs_by_id[m_cands[0].viirs_observation_id] if m_cands else None
                )
                rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    modis_observation_id=m_id,
                    viirs_observation_id=first_v.observation_id if first_v else None,
                    match_status=MatchStatus.AMBIGUOUS,
                    spatial_distance_m=m_cands[0].spatial_distance_m if m_cands else None,
                    time_difference_s=m_cands[0].time_difference_s if m_cands else None,
                    matching_method_version=method_version,
                    matching_parameters=parameters,
                    match_score=m_cands[0].score if m_cands else None,
                    review_status=ReviewStatus.FLAGGED_DISCREPANCY,
                    provenance=HarmonisedRecordProvenance(
                        modis_source_record_id=m_obs.source_record_id,
                        viirs_source_record_id=first_v.source_record_id if first_v else None,
                        modis_product_version=m_obs.product_version,
                        viirs_product_version=first_v.product_version if first_v else None,
                        score_formula_note=cls.SCORE_DEFINITION,
                        candidate_count=len(m_cands),
                        decision_reason=f"ambiguous_cluster_modis_deg_{len(m_cands)}",
                    ),
                    modis_observation=m_obs,
                    viirs_observation=first_v,
                    candidate_links=m_cands,
                )
                harmonised_records.append(rec)

        elif policy == AmbiguityPolicy.ONE_TO_ONE_DETERMINISTIC:
            # Sort deterministically by: (-score, spatial_distance_m, time_difference_s, modis_source_record_id, viirs_source_record_id)
            def sort_key(c: MatchCandidateRecord):
                m_rec = modis_by_id[c.modis_observation_id]
                v_rec = viirs_by_id[c.viirs_observation_id]
                return (
                    -(c.score if c.score is not None else 0.0),
                    c.spatial_distance_m,
                    c.time_difference_s,
                    m_rec.source_record_id,
                    v_rec.source_record_id,
                )

            sorted_cands = sorted(candidates, key=sort_key)
            assigned_m: Set[str] = set()
            assigned_v: Set[str] = set()

            for cand in sorted_cands:
                m_id = cand.modis_observation_id
                v_id = cand.viirs_observation_id

                if m_id not in assigned_m and v_id not in assigned_v:
                    cand.decision = CandidateDecision.ACCEPTED
                    cand.decision_reason = "deterministic_best_score_1_to_1"
                    assigned_m.add(m_id)
                    assigned_v.add(v_id)
                    matched_modis_ids.add(m_id)
                    matched_viirs_ids.add(v_id)

                    m_obs = modis_by_id[m_id]
                    v_obs = viirs_by_id[v_id]
                    rec = HarmonisedRecord(
                        harmonisation_id=f"harm-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        modis_observation_id=m_id,
                        viirs_observation_id=v_id,
                        match_status=MatchStatus.MATCHED,
                        spatial_distance_m=cand.spatial_distance_m,
                        time_difference_s=cand.time_difference_s,
                        matching_method_version=method_version,
                        matching_parameters=parameters,
                        match_score=cand.score,
                        review_status=ReviewStatus.UNREVIEWED,
                        provenance=HarmonisedRecordProvenance(
                            modis_source_record_id=m_obs.source_record_id,
                            viirs_source_record_id=v_obs.source_record_id,
                            modis_product_version=m_obs.product_version,
                            viirs_product_version=v_obs.product_version,
                            score_formula_note=cls.SCORE_DEFINITION,
                            candidate_count=len(modis_candidates_map[m_id]),
                            decision_reason="deterministic_best_score_1_to_1",
                        ),
                        modis_observation=m_obs,
                        viirs_observation=v_obs,
                        candidate_links=[cand],
                    )
                    harmonised_records.append(rec)
                else:
                    cand.decision = CandidateDecision.REJECTED
                    cand.decision_reason = "superseded_by_higher_ranked_candidate"

        elif policy == AmbiguityPolicy.MANY_TO_MANY:
            for cand in candidates:
                cand.decision = CandidateDecision.ACCEPTED
                cand.decision_reason = "accepted_under_many_to_many_policy"
                m_id = cand.modis_observation_id
                v_id = cand.viirs_observation_id
                matched_modis_ids.add(m_id)
                matched_viirs_ids.add(v_id)

                m_obs = modis_by_id[m_id]
                v_obs = viirs_by_id[v_id]
                rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    modis_observation_id=m_id,
                    viirs_observation_id=v_id,
                    match_status=MatchStatus.MATCHED,
                    spatial_distance_m=cand.spatial_distance_m,
                    time_difference_s=cand.time_difference_s,
                    matching_method_version=method_version,
                    matching_parameters=parameters,
                    match_score=cand.score,
                    review_status=ReviewStatus.UNREVIEWED,
                    provenance=HarmonisedRecordProvenance(
                        modis_source_record_id=m_obs.source_record_id,
                        viirs_source_record_id=v_obs.source_record_id,
                        modis_product_version=m_obs.product_version,
                        viirs_product_version=v_obs.product_version,
                        score_formula_note=cls.SCORE_DEFINITION,
                        candidate_count=len(modis_candidates_map[m_id]),
                        decision_reason="accepted_under_many_to_many_policy",
                    ),
                    modis_observation=m_obs,
                    viirs_observation=v_obs,
                    candidate_links=[cand],
                )
                harmonised_records.append(rec)

        # Step 4: Unmatched Preservation (Stage G, FR-12)
        # 1. Unmatched MODIS (deg == 0 or all candidates superseded)
        for m_obs in m_eligible:
            m_id = m_obs.observation_id
            if m_id not in matched_modis_ids and m_id not in ambiguous_modis_ids:
                superseded_cands = modis_candidates_map.get(m_id, [])
                dec_reason = (
                    "No VIIRS candidate detected within spatial and temporal thresholds"
                    if not superseded_cands
                    else "All candidate VIIRS partners superseded by higher ranked competitors"
                )
                rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    modis_observation_id=m_id,
                    viirs_observation_id=None,
                    match_status=MatchStatus.UNMATCHED_MODIS,
                    spatial_distance_m=None,
                    time_difference_s=None,
                    matching_method_version=method_version,
                    matching_parameters=parameters,
                    match_score=None,
                    review_status=ReviewStatus.UNREVIEWED,
                    provenance=HarmonisedRecordProvenance(
                        modis_source_record_id=m_obs.source_record_id,
                        modis_product_version=m_obs.product_version,
                        candidate_count=len(superseded_cands),
                        decision_reason=dec_reason,
                    ),
                    modis_observation=m_obs,
                    viirs_observation=None,
                    candidate_links=superseded_cands,
                )
                harmonised_records.append(rec)

        # 2. Unmatched VIIRS (deg == 0 or all candidates superseded)
        for v_obs in v_eligible:
            v_id = v_obs.observation_id
            if v_id not in matched_viirs_ids and v_id not in ambiguous_viirs_ids:
                superseded_cands = viirs_candidates_map.get(v_id, [])
                dec_reason = (
                    "No MODIS candidate detected within spatial and temporal thresholds"
                    if not superseded_cands
                    else "All candidate MODIS partners superseded by higher ranked competitors"
                )
                rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    modis_observation_id=None,
                    viirs_observation_id=v_id,
                    match_status=MatchStatus.UNMATCHED_VIIRS,
                    spatial_distance_m=None,
                    time_difference_s=None,
                    matching_method_version=method_version,
                    matching_parameters=parameters,
                    match_score=None,
                    review_status=ReviewStatus.UNREVIEWED,
                    provenance=HarmonisedRecordProvenance(
                        viirs_source_record_id=v_obs.source_record_id,
                        viirs_product_version=v_obs.product_version,
                        candidate_count=len(superseded_cands),
                        decision_reason=dec_reason,
                    ),
                    modis_observation=None,
                    viirs_observation=v_obs,
                    candidate_links=superseded_cands,
                )
                harmonised_records.append(rec)

        # Step 5: Construct 6 Required Outputs
        unmatched_modis = [
            r for r in harmonised_records if r.match_status == MatchStatus.UNMATCHED_MODIS
        ]
        unmatched_viirs = [
            r for r in harmonised_records if r.match_status == MatchStatus.UNMATCHED_VIIRS
        ]
        ambiguous = [
            r for r in harmonised_records if r.match_status == MatchStatus.AMBIGUOUS
        ]
        matched = [
            r for r in harmonised_records if r.match_status == MatchStatus.MATCHED
        ]

        m_valid_cnt = len(m_eligible)
        v_valid_cnt = len(v_eligible)

        m_match_rate = (
            round((len(matched_modis_ids) / m_valid_cnt) * 100.0, 2)
            if m_valid_cnt > 0
            else 0.0
        )
        v_match_rate = (
            round((len(matched_viirs_ids) / v_valid_cnt) * 100.0, 2)
            if v_valid_cnt > 0
            else 0.0
        )
        amb_rate = (
            round((len(ambiguous_modis_ids) / max(len(candidates), 1)) * 100.0, 2)
            if candidates
            else 0.0
        )

        elapsed_ms = round((time.time() - start_wall_time) * 1000.0, 2)

        counts = ProcessingRunCounts(
            modis_input_rows=modis_input_count or m_valid_cnt,
            viirs_input_rows=viirs_input_count or v_valid_cnt,
            modis_valid_rows=m_valid_cnt,
            viirs_valid_rows=v_valid_cnt,
            modis_warning_rows=modis_warning_count,
            viirs_warning_rows=viirs_warning_count,
            modis_rejected_rows=modis_rejected_count,
            viirs_rejected_rows=viirs_rejected_count,
            matched_count=len(matched),
            unmatched_modis_count=len(unmatched_modis),
            unmatched_viirs_count=len(unmatched_viirs),
            ambiguous_count=len(ambiguous),
            total_candidate_pairs=len(candidates),
        )

        rates = ProcessingRunRates(
            modis_match_rate=m_match_rate,
            modis_match_rate_denominator=f"valid MODIS rows ({m_valid_cnt})",
            viirs_match_rate=v_match_rate,
            viirs_match_rate_denominator=f"valid VIIRS rows ({v_valid_cnt})",
            ambiguity_rate=amb_rate,
            ambiguity_rate_denominator=f"total candidate pairs ({len(candidates)})",
        )

        summary = ProcessingRunSummary(
            run_id=run_id,
            started_at=started_at_iso,
            completed_at=datetime.now().isoformat(),
            status=RunStatus.SUCCEEDED,
            method_version=method_version,
            parameters=parameters,
            input_dataset_ids=InputDatasetIds(
                modis_dataset_id=m_eligible[0].dataset_id if m_eligible else None,
                viirs_dataset_id=v_eligible[0].dataset_id if v_eligible else None,
            ),
            counts=counts,
            rates=rates,
            warnings=[
                f"Candidate generation used STRtree spatial indexing and WGS 84 geodesic distance.",
                f"Ambiguity policy applied: {policy.value}.",
                f"Runtime: {elapsed_ms}ms.",
            ],
            is_test_fixture=False,
        )

        return HarmonisationEngineResult(
            match_candidates=candidates,
            harmonised_records=harmonised_records,
            unmatched_modis_records=unmatched_modis,
            unmatched_viirs_records=unmatched_viirs,
            ambiguous_records=ambiguous,
            summary_report=summary,
        )


# Backwards compatibility alias
MatchingEngine = MatchingEngineService
