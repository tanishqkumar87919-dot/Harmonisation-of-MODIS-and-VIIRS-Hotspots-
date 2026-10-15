"""Scientific evaluation and sensitivity analysis service."""

from typing import List, Tuple
from backend.app.schemas.common import MatchStatus
from backend.app.schemas.matching import HarmonisedRecord, MatchingParameters
from backend.app.schemas.observation import StandardizedObservation
from backend.app.schemas.run import (
    BaselineComparisonMetrics,
    DistributionBin,
    FrpDistribution,
    ProcessingRunSummary,
    RunDetailedEvaluation,
    SensitivityGridPoint,
)
from backend.app.services.matching import MatchingEngine


class EvaluationService:
    """
    Computes rigorous empirical evaluation metrics for a harmonisation run:
    - Comparative baselines (Raw concatenation vs. Harmonised).
    - Threshold sensitivity sweep across distance and time parameters.
    - Spatial distance and time delta empirical distributions.
    - Sensor-specific FRP distributions with scientific non-equivalence disclaimer.
    """

    SPATIAL_BINS = [
        ("0–250m", 0.0, 250.0),
        ("250–500m", 250.0, 500.0),
        ("500–1000m", 500.0, 1000.0),
        ("1000–1500m", 1000.0, 1500.0),
        (">1500m", 1500.0, float("inf")),
    ]

    TEMPORAL_BINS = [
        ("0–15 min", 0.0, 900.0),
        ("15–30 min", 900.0, 1800.0),
        ("30–45 min", 1800.0, 2700.0),
        ("45–60 min", 2700.0, 3600.0),
        (">60 min", 3600.0, float("inf")),
    ]

    FRP_BINS = [
        ("0–10 MW", 0.0, 10.0),
        ("10–25 MW", 10.0, 25.0),
        ("25–50 MW", 25.0, 50.0),
        ("50–100 MW", 50.0, 100.0),
        (">100 MW", 100.0, float("inf")),
    ]

    @classmethod
    def generate_evaluation(
        cls,
        summary: ProcessingRunSummary,
        records: List[HarmonisedRecord],
        modis_observations: List[StandardizedObservation],
        viirs_observations: List[StandardizedObservation],
    ) -> RunDetailedEvaluation:
        """
        Generate detailed evaluation metrics for a completed harmonisation run.
        """
        # 1. Baseline Comparisons
        total_modis = len(modis_observations)
        total_viirs = len(viirs_observations)
        raw_total = total_modis + total_viirs

        # Baseline 1: Raw Unharmonised Concatenation
        # Approximate colocated duplicates in raw union
        raw_unique_locations = len(
            {(round(obs.latitude, 2), round(obs.longitude, 2)) for obs in modis_observations + viirs_observations}
        )
        raw_dup_est = max(0, raw_total - raw_unique_locations)

        # Baseline 2: Time-Window Coincidence Only (no spatial filter)
        time_only_matches = 0
        for m in modis_observations:
            m_dt = MatchingEngine.parse_iso_utc(m.observation_time_utc)
            for v in viirs_observations:
                v_dt = MatchingEngine.parse_iso_utc(v.observation_time_utc)
                if abs((m_dt - v_dt).total_seconds()) <= summary.parameters.max_time_difference_seconds:
                    time_only_matches += 1
                    break

        baselines = [
            BaselineComparisonMetrics(
                name="Raw Concatenation (Unharmonised)",
                description="Direct naive merge of MODIS and VIIRS records without deduplication or spatial correlation.",
                total_records=raw_total,
                unique_time_locations=raw_unique_locations,
                duplicate_estimate=raw_dup_est,
            ),
            BaselineComparisonMetrics(
                name="Temporal Co-occurrence Only",
                description="Matches observations purely based on satellite overpass time window without spatial proximity.",
                total_records=time_only_matches,
                unique_time_locations=raw_unique_locations,
                duplicate_estimate=max(0, time_only_matches - summary.counts.matched_count),
            ),
            BaselineComparisonMetrics(
                name="Harmonised Matching Model (This Run)",
                description="Scientifically constrained spatial-temporal colocation preserving sensor provenance and ambiguity.",
                total_records=len(records),
                unique_time_locations=summary.counts.matched_count + summary.counts.ambiguous_count + summary.counts.unmatched_modis_count + summary.counts.unmatched_viirs_count,
                duplicate_estimate=0,
            ),
        ]

        # 2. Sensitivity Grid (Evaluation across multiple parameter thresholds)
        spatial_thresholds = [500.0, 1000.0, 1500.0, 2500.0]
        temporal_thresholds = [1800.0, 3600.0, 7200.0]
        sensitivity_grid: List[SensitivityGridPoint] = []

        for s_thresh in spatial_thresholds:
            for t_thresh in temporal_thresholds:
                test_params = MatchingParameters(
                    max_distance_meters=s_thresh,
                    max_time_difference_seconds=t_thresh,
                    ambiguity_policy=summary.parameters.ambiguity_policy,
                    matching_method_version=summary.method_version,
                    quality_filters=summary.parameters.quality_filters,
                )
                _, _, test_summary = MatchingEngine.execute_matching_run(
                    run_id=f"sens-{int(s_thresh)}-{int(t_thresh)}",
                    modis_observations=modis_observations,
                    viirs_observations=viirs_observations,
                    parameters=test_params,
                )
                sensitivity_grid.append(
                    SensitivityGridPoint(
                        spatial_threshold_m=s_thresh,
                        temporal_threshold_s=t_thresh,
                        matched_count=test_summary.counts.matched_count,
                        ambiguous_count=test_summary.counts.ambiguous_count,
                        unmatched_modis_count=test_summary.counts.unmatched_modis_count,
                        unmatched_viirs_count=test_summary.counts.unmatched_viirs_count,
                        match_rate=test_summary.rates.modis_match_rate,
                    )
                )

        # 3. Spatial Distance Distribution of Matched Pairs
        matched_records = [r for r in records if r.match_status == MatchStatus.MATCHED and r.spatial_distance_m is not None]
        spatial_dist_bins = {name: 0 for name, _, _ in cls.SPATIAL_BINS}
        for rec in matched_records:
            d = rec.spatial_distance_m or 0.0
            for name, low, high in cls.SPATIAL_BINS:
                if low <= d < high or (high == float("inf") and d >= low):
                    spatial_dist_bins[name] += 1
                    break

        spatial_distribution = [
            DistributionBin(bin=name, count=count) for name, count in spatial_dist_bins.items()
        ]

        # 4. Time Difference Distribution of Matched Pairs
        temporal_dist_bins = {name: 0 for name, _, _ in cls.TEMPORAL_BINS}
        for rec in matched_records:
            dt = rec.time_difference_s or 0.0
            for name, low, high in cls.TEMPORAL_BINS:
                if low <= dt < high or (high == float("inf") and dt >= low):
                    temporal_dist_bins[name] += 1
                    break

        time_distribution = [
            DistributionBin(bin=name, count=count) for name, count in temporal_dist_bins.items()
        ]

        # 5. FRP Distribution (Strictly separate without cross-sensor averaging)
        modis_frp_bins = {name: 0 for name, _, _ in cls.FRP_BINS}
        for m in modis_observations:
            if m.frp_raw is not None:
                val = m.frp_raw
                for name, low, high in cls.FRP_BINS:
                    if low <= val < high or (high == float("inf") and val >= low):
                        modis_frp_bins[name] += 1
                        break

        viirs_frp_bins = {name: 0 for name, _, _ in cls.FRP_BINS}
        for v in viirs_observations:
            if v.frp_raw is not None:
                val = v.frp_raw
                for name, low, high in cls.FRP_BINS:
                    if low <= val < high or (high == float("inf") and val >= low):
                        viirs_frp_bins[name] += 1
                        break

        frp_dist = FrpDistribution(
            modis_frp=[DistributionBin(bin=k, count=v) for k, v in modis_frp_bins.items()],
            viirs_frp=[DistributionBin(bin=k, count=v) for k, v in viirs_frp_bins.items()],
            scientific_disclaimer=(
                "FRP (Fire Radiative Power in MW) is plotted on separate sensor axes. "
                "MODIS (1 km nadir pixel) and VIIRS (375 m nadir pixel) integrate radiative emissions over different footprints. "
                "Per research methodology rules, FRP values must not be averaged or assumed directly interchangeable."
            ),
        )

        return RunDetailedEvaluation(
            run_id=summary.run_id,
            baselines=baselines,
            sensitivity_grid=sensitivity_grid,
            spatial_distance_distribution=spatial_distribution,
            time_difference_distribution=time_distribution,
            frp_distribution=frp_dist,
        )
