"""Spatial-temporal matching and harmonisation engine for MODIS and VIIRS hotspots."""

import math
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from backend.app.schemas.common import (
    AmbiguityPolicy,
    CandidateDecision,
    MatchStatus,
    ReviewStatus,
    TimeWindowRule,
)
from backend.app.schemas.matching import (
    HarmonisedRecord,
    HarmonisedRecordProvenance,
    MatchCandidateRecord,
    MatchingParameters,
)
from backend.app.schemas.observation import StandardizedObservation
from backend.app.schemas.run import (
    InputDatasetIds,
    ProcessingRunCounts,
    ProcessingRunRates,
    ProcessingRunSummary,
    RunStatus,
)


class MatchingEngine:
    """
    Core scientific matching engine.
    Executes Stages D through G from docs/05_HARMONISATION_ALGORITHM.md:
    - Candidate generation using geodesic distance and UTC temporal deltas.
    - Transparent normalized ranking score (explicitly non-probabilistic).
    - Policy-governed ambiguity resolution (retain_ambiguous, one_to_one_deterministic, many_to_many).
    - Complete preservation of unmatched MODIS and VIIRS observations.
    """

    EARTH_RADIUS_METERS = 6371000.0

    @classmethod
    def haversine_distance_meters(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates great-circle distance between two geographic points in metres.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_METERS * c

    @classmethod
    def parse_iso_utc(cls, dt_str: str) -> datetime:
        """Parse ISO 8601 UTC timestamp."""
        # Replace trailing Z with +00:00 for fromisoformat compatibility
        clean = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)

    @classmethod
    def calculate_ranking_score(
        cls,
        dist_m: float,
        dt_s: float,
        max_dist_m: float,
        max_dt_s: float,
        spatial_weight: float = 0.5,
        temporal_weight: float = 0.5,
    ) -> float:
        """
        Calculates a transparent heuristic ranking score in [0.0, 1.0].
        Note: This is strictly a relative ranking metric, NOT a calibrated probability.
        """
        norm_dist = min(dist_m / max(max_dist_m, 1.0), 1.0)
        norm_time = min(dt_s / max(max_dt_s, 1.0), 1.0)
        score = 1.0 - (spatial_weight * norm_dist + temporal_weight * norm_time)
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def execute_matching_run(
        cls,
        run_id: str,
        modis_observations: List[StandardizedObservation],
        viirs_observations: List[StandardizedObservation],
        parameters: MatchingParameters,
        modis_input_count: int = 0,
        viirs_input_count: int = 0,
        modis_warning_count: int = 0,
        viirs_warning_count: int = 0,
        modis_rejected_count: int = 0,
        viirs_rejected_count: int = 0,
    ) -> Tuple[List[HarmonisedRecord], List[MatchCandidateRecord], ProcessingRunSummary]:
        """
        Executes a complete harmonisation run across eligible MODIS and VIIRS records.
        """
        start_time_iso = datetime.now().isoformat()
        max_dist = parameters.max_distance_meters
        max_time = parameters.max_time_difference_seconds
        policy = parameters.ambiguity_policy
        method_version = parameters.matching_method_version

        s_weight = parameters.score_weights.spatial_weight if parameters.score_weights else 0.5
        t_weight = parameters.score_weights.temporal_weight if parameters.score_weights else 0.5

        # Maps for quick lookup
        modis_by_id = {obs.observation_id: obs for obs in modis_observations}
        viirs_by_id = {obs.observation_id: obs for obs in viirs_observations}

        # Parse observation datetimes once
        modis_dts = {obs.observation_id: cls.parse_iso_utc(obs.observation_time_utc) for obs in modis_observations}
        viirs_dts = {obs.observation_id: cls.parse_iso_utc(obs.observation_time_utc) for obs in viirs_observations}

        # Stage D: Candidate Pair Generation
        candidates: List[MatchCandidateRecord] = []
        modis_candidates_map: Dict[str, List[MatchCandidateRecord]] = {obs.observation_id: [] for obs in modis_observations}
        viirs_candidates_map: Dict[str, List[MatchCandidateRecord]] = {obs.observation_id: [] for obs in viirs_observations}

        for m_obs in modis_observations:
            m_id = m_obs.observation_id
            m_dt = modis_dts[m_id]
            m_lat, m_lon = m_obs.latitude, m_obs.longitude

            for v_obs in viirs_observations:
                v_id = v_obs.observation_id
                v_dt = viirs_dts[v_id]

                # Temporal filter
                time_diff_s = abs((m_dt - v_dt).total_seconds())
                if time_diff_s > max_time:
                    continue

                # Spatial filter
                dist_m = cls.haversine_distance_meters(m_lat, m_lon, v_obs.latitude, v_obs.longitude)
                if dist_m > max_dist:
                    continue

                # Compute ranking score
                score = cls.calculate_ranking_score(dist_m, time_diff_s, max_dist, max_time, s_weight, t_weight)

                cand = MatchCandidateRecord(
                    id=f"cand-{uuid.uuid4().hex[:10]}",
                    run_id=run_id,
                    modis_observation_id=m_id,
                    viirs_observation_id=v_id,
                    spatial_distance_m=round(dist_m, 2),
                    time_difference_s=round(time_diff_s, 2),
                    score=score,
                    decision=CandidateDecision.PENDING,
                    decision_reason="Generated within spatial and temporal thresholds",
                )
                candidates.append(cand)
                modis_candidates_map[m_id].append(cand)
                viirs_candidates_map[v_id].append(cand)

        # Stage F: Ambiguity Resolution according to configured policy
        harmonised_records: List[HarmonisedRecord] = []
        matched_modis_ids: Set[str] = set()
        matched_viirs_ids: Set[str] = set()
        ambiguous_modis_ids: Set[str] = set()
        ambiguous_viirs_ids: Set[str] = set()

        score_note = "Heuristic ranking score: 1.0 - (0.5*(dist/max_dist) + 0.5*(dt/max_dt)). Not a probability."

        if policy == AmbiguityPolicy.RETAIN_AMBIGUOUS:
            # 1:1 unambiguous pairings are accepted as MATCHED.
            # Multi-candidate pairings are retained and flagged as AMBIGUOUS.
            for m_id, m_cands in modis_candidates_map.items():
                if len(m_cands) == 1:
                    cand = m_cands[0]
                    v_id = cand.viirs_observation_id
                    v_cands = viirs_candidates_map[v_id]
                    if len(v_cands) == 1:
                        # Mutually exclusive single pair -> Match!
                        cand.decision = CandidateDecision.ACCEPTED
                        cand.decision_reason = "Unique 1:1 mutual candidate pairing"
                        matched_modis_ids.add(m_id)
                        matched_viirs_ids.add(v_id)

                        m_obs = modis_by_id[m_id]
                        v_obs = viirs_by_id[v_id]
                        harm_rec = HarmonisedRecord(
                            harmonisation_id=f"harm-{uuid.uuid4().hex[:10]}",
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
                                score_formula_note=score_note,
                                candidate_count=1,
                                decision_reason="Unique 1:1 mutual candidate pairing",
                            ),
                            modis_observation=m_obs,
                            viirs_observation=v_obs,
                            candidate_links=[cand],
                        )
                        harmonised_records.append(harm_rec)
                    else:
                        # VIIRS has multiple candidates
                        ambiguous_modis_ids.add(m_id)
                        ambiguous_viirs_ids.add(v_id)
                elif len(m_cands) > 1:
                    ambiguous_modis_ids.add(m_id)
                    for c in m_cands:
                        ambiguous_viirs_ids.add(c.viirs_observation_id)

            # Record ambiguous groups
            for m_id in ambiguous_modis_ids:
                m_cands = modis_candidates_map[m_id]
                for c in m_cands:
                    c.decision = CandidateDecision.AMBIGUOUS
                    c.decision_reason = f"Ambiguous association under {policy.value}: multiple candidates co-occur"

                m_obs = modis_by_id[m_id]
                v_ids = [c.viirs_observation_id for c in m_cands]
                first_v = viirs_by_id[v_ids[0]] if v_ids else None
                harm_rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:10]}",
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
                        score_formula_note=score_note,
                        candidate_count=len(m_cands),
                        decision_reason=f"Ambiguous: {len(m_cands)} VIIRS candidate detections compete for this MODIS footprint",
                    ),
                    modis_observation=m_obs,
                    viirs_observation=first_v,
                    candidate_links=m_cands,
                )
                harmonised_records.append(harm_rec)

        elif policy == AmbiguityPolicy.ONE_TO_ONE_DETERMINISTIC:
            # Deterministic greedy assignment by highest ranking score (lowest distance/time)
            sorted_candidates = sorted(candidates, key=lambda c: (c.score or 0.0, -c.spatial_distance_m), reverse=True)
            assigned_modis: Set[str] = set()
            assigned_viirs: Set[str] = set()

            for cand in sorted_candidates:
                m_id = cand.modis_observation_id
                v_id = cand.viirs_observation_id

                if m_id not in assigned_modis and v_id not in assigned_viirs:
                    # Accept pair
                    cand.decision = CandidateDecision.ACCEPTED
                    cand.decision_reason = "Selected as optimal deterministic 1:1 pair by ranking score"
                    assigned_modis.add(m_id)
                    assigned_viirs.add(v_id)
                    matched_modis_ids.add(m_id)
                    matched_viirs_ids.add(v_id)

                    m_obs = modis_by_id[m_id]
                    v_obs = viirs_by_id[v_id]
                    harm_rec = HarmonisedRecord(
                        harmonisation_id=f"harm-{uuid.uuid4().hex[:10]}",
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
                            score_formula_note=score_note,
                            candidate_count=len(modis_candidates_map[m_id]),
                            decision_reason="Selected as optimal deterministic 1:1 pair by ranking score",
                        ),
                        modis_observation=m_obs,
                        viirs_observation=v_obs,
                        candidate_links=[cand],
                    )
                    harmonised_records.append(harm_rec)
                else:
                    cand.decision = CandidateDecision.REJECTED
                    cand.decision_reason = "Competitor candidate had higher heuristic rank"

        elif policy == AmbiguityPolicy.MANY_TO_MANY:
            # Retain every valid candidate pairing as a co-occurring cluster link
            for cand in candidates:
                cand.decision = CandidateDecision.ACCEPTED
                cand.decision_reason = "Accepted under many-to-many cluster policy"
                m_id = cand.modis_observation_id
                v_id = cand.viirs_observation_id
                matched_modis_ids.add(m_id)
                matched_viirs_ids.add(v_id)

                m_obs = modis_by_id[m_id]
                v_obs = viirs_by_id[v_id]
                harm_rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:10]}",
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
                        score_formula_note=score_note,
                        candidate_count=len(modis_candidates_map[m_id]),
                        decision_reason="Accepted under many-to-many cluster policy",
                    ),
                    modis_observation=m_obs,
                    viirs_observation=v_obs,
                    candidate_links=[cand],
                )
                harmonised_records.append(harm_rec)

        # Stage G: Preserve UNMATCHED records (Never discard unmatched detections)
        # 1. Unmatched MODIS
        for m_obs in modis_observations:
            m_id = m_obs.observation_id
            if m_id not in matched_modis_ids and m_id not in ambiguous_modis_ids:
                harm_rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:10]}",
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
                        candidate_count=0,
                        decision_reason="No VIIRS observation detected within configured spatial/temporal windows",
                    ),
                    modis_observation=m_obs,
                    viirs_observation=None,
                    candidate_links=[],
                )
                harmonised_records.append(harm_rec)

        # 2. Unmatched VIIRS
        for v_obs in viirs_observations:
            v_id = v_obs.observation_id
            if v_id not in matched_viirs_ids and v_id not in ambiguous_viirs_ids:
                harm_rec = HarmonisedRecord(
                    harmonisation_id=f"harm-{uuid.uuid4().hex[:10]}",
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
                        candidate_count=0,
                        decision_reason="No MODIS observation detected within configured spatial/temporal windows",
                    ),
                    modis_observation=None,
                    viirs_observation=v_obs,
                    candidate_links=[],
                )
                harmonised_records.append(harm_rec)

        # Compute summary counts
        matched_cnt = sum(1 for r in harmonised_records if r.match_status == MatchStatus.MATCHED)
        unmatched_m_cnt = sum(1 for r in harmonised_records if r.match_status == MatchStatus.UNMATCHED_MODIS)
        unmatched_v_cnt = sum(1 for r in harmonised_records if r.match_status == MatchStatus.UNMATCHED_VIIRS)
        ambiguous_cnt = sum(1 for r in harmonised_records if r.match_status == MatchStatus.AMBIGUOUS)

        modis_valid_cnt = len(modis_observations)
        viirs_valid_cnt = len(viirs_observations)

        # Calculate scientific rates with explicit denominators
        m_rate = round((len(matched_modis_ids) / modis_valid_cnt) * 100.0, 1) if modis_valid_cnt > 0 else 0.0
        v_rate = round((len(matched_viirs_ids) / viirs_valid_cnt) * 100.0, 1) if viirs_valid_cnt > 0 else 0.0
        amb_rate = round((len(ambiguous_modis_ids) / max(len(candidates), 1)) * 100.0, 1) if candidates else 0.0

        counts = ProcessingRunCounts(
            modis_input_rows=modis_input_count or modis_valid_cnt,
            viirs_input_rows=viirs_input_count or viirs_valid_cnt,
            modis_valid_rows=modis_valid_cnt,
            viirs_valid_rows=viirs_valid_cnt,
            modis_warning_rows=modis_warning_count,
            viirs_warning_rows=viirs_warning_count,
            modis_rejected_rows=modis_rejected_count,
            viirs_rejected_rows=viirs_rejected_count,
            matched_count=matched_cnt,
            unmatched_modis_count=unmatched_m_cnt,
            unmatched_viirs_count=unmatched_v_cnt,
            ambiguous_count=ambiguous_cnt,
            total_candidate_pairs=len(candidates),
        )

        rates = ProcessingRunRates(
            modis_match_rate=m_rate,
            modis_match_rate_denominator=f"valid MODIS rows ({modis_valid_cnt})",
            viirs_match_rate=v_rate,
            viirs_match_rate_denominator=f"valid VIIRS rows ({viirs_valid_cnt})",
            ambiguity_rate=amb_rate,
            ambiguity_rate_denominator=f"total candidate pairs ({len(candidates)})",
        )

        run_summary = ProcessingRunSummary(
            run_id=run_id,
            started_at=start_time_iso,
            completed_at=datetime.now().isoformat(),
            status=RunStatus.SUCCEEDED,
            method_version=method_version,
            parameters=parameters,
            input_dataset_ids=InputDatasetIds(
                modis_dataset_id=modis_observations[0].dataset_id if modis_observations else None,
                viirs_dataset_id=viirs_observations[0].dataset_id if viirs_observations else None,
            ),
            counts=counts,
            rates=rates,
            warnings=[
                f"Candidate distance computed using WGS-84 Haversine spherical projection.",
                f"Matching policy applied: {policy.value}.",
            ],
            is_test_fixture=False,
        )

        return harmonised_records, candidates, run_summary
