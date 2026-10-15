"""Scientific evaluation and sensitivity analysis service adhering to docs/03_RESEARCH_METHODOLOGY.md."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.schemas.common import MatchStatus
from backend.app.schemas.matching import HarmonisedRecord, MatchingParameters
from backend.app.schemas.observations import StandardizedObservationSchema
from backend.app.schemas.runs import (
    BaselineComparisonMetrics,
    DistributionBin,
    FrpDistribution,
    ProcessingRunSummary,
    RunDetailedEvaluation,
    SensitivityGridPoint,
)
from backend.app.services.matching_engine import MatchingEngineService


class EvaluationService:
    """
    Computes rigorous empirical evaluation metrics for a harmonisation run:
    - Four mandatory baselines (MODIS-only, VIIRS-only, Naive concatenation, Proposed harmonisation).
    - Threshold sensitivity grid sweep across configurable distance and time parameters.
    - Empirical distributions: spatial distance, time difference, hourly temporal activity.
    - Side-by-side FRP percentiles with scientific disclaimer.
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
    def compute_frp_percentiles(cls, frp_values: List[float]) -> Dict[str, float]:
        """Compute p10, p25, p50 (median), p75, p90 for FRP values."""
        if not frp_values:
            return {"p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0, "mean": 0.0}
        arr = np.array(frp_values)
        return {
            "p10": round(float(np.percentile(arr, 10)), 2),
            "p25": round(float(np.percentile(arr, 25)), 2),
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p75": round(float(np.percentile(arr, 75)), 2),
            "p90": round(float(np.percentile(arr, 90)), 2),
            "mean": round(float(np.mean(arr)), 2),
        }

    @classmethod
    def compute_four_baselines(
        cls,
        modis_obs: List[StandardizedObservationSchema],
        viirs_obs: List[StandardizedObservationSchema],
        records: List[HarmonisedRecord],
        summary: ProcessingRunSummary,
    ) -> Tuple[List[BaselineComparisonMetrics], Dict[str, Any]]:
        """
        Compute the four mandatory baselines specified in docs/03_RESEARCH_METHODOLOGY.md Section 5:
        1. modis_only
        2. viirs_only
        3. naive_concatenation
        4. proposed_harmonisation
        """
        # MODIS only metrics
        m_frps = [m.frp_raw for m in modis_obs if m.frp_raw is not None]
        m_lats = [m.latitude for m in modis_obs]
        m_lons = [m.longitude for m in modis_obs]
        m_times = [m.observation_time_utc for m in modis_obs if m.observation_time_utc]
        m_stats = cls.compute_frp_percentiles(m_frps)
        modis_only_detail = {
            "valid_modis_count": len(modis_obs),
            "date_range": [min(m_times), max(m_times)] if m_times else None,
            "bbox": [min(m_lons), min(m_lats), max(m_lons), max(m_lats)] if m_lons else None,
            "frp_mean": m_stats["mean"],
            "frp_median": m_stats["p50"],
        }

        # VIIRS only metrics
        v_frps = [v.frp_raw for v in viirs_obs if v.frp_raw is not None]
        v_lats = [v.latitude for v in viirs_obs]
        v_lons = [v.longitude for v in viirs_obs]
        v_times = [v.observation_time_utc for v in viirs_obs if v.observation_time_utc]
        v_stats = cls.compute_frp_percentiles(v_frps)
        viirs_only_detail = {
            "valid_viirs_count": len(viirs_obs),
            "date_range": [min(v_times), max(v_times)] if v_times else None,
            "bbox": [min(v_lons), min(v_lats), max(v_lons), max(v_lats)] if v_lons else None,
            "frp_mean": v_stats["mean"],
            "frp_median": v_stats["p50"],
        }

        # Naive concatenation metrics
        total_naive = len(modis_obs) + len(viirs_obs)
        matched_pairs_count = summary.counts.matched_count
        naive_detail = {
            "total_naive_count": total_naive,
            "estimated_duplicate_overlap_count": matched_pairs_count,
        }

        # Proposed harmonisation metrics
        harmonisation_detail = {
            "matched_count": summary.counts.matched_count,
            "unmatched_modis_count": summary.counts.unmatched_modis_count,
            "unmatched_viirs_count": summary.counts.unmatched_viirs_count,
            "ambiguous_count": summary.counts.ambiguous_count,
            "distinct_harmonised_records_count": len(records),
            "modis_match_rate": summary.rates.modis_match_rate,
            "modis_match_rate_denominator": "valid_and_warning_modis_observations",
            "viirs_match_rate": summary.rates.viirs_match_rate,
            "viirs_match_rate_denominator": "valid_and_warning_viirs_observations",
        }

        four_baselines_dict = {
            "modis_only": modis_only_detail,
            "viirs_only": viirs_only_detail,
            "naive_concatenation": naive_detail,
            "proposed_harmonisation": harmonisation_detail,
        }

        baselines_list = [
            BaselineComparisonMetrics(
                name="MODIS Only Baseline",
                description=f"Isolated MODIS observations ({len(modis_obs)} detections). Mean FRP: {m_stats['mean']} MW.",
                total_records=len(modis_obs),
                unique_time_locations=len(modis_obs),
                duplicate_estimate=0,
            ),
            BaselineComparisonMetrics(
                name="VIIRS Only Baseline",
                description=f"Isolated VIIRS observations ({len(viirs_obs)} detections). Mean FRP: {v_stats['mean']} MW.",
                total_records=len(viirs_obs),
                unique_time_locations=len(viirs_obs),
                duplicate_estimate=0,
            ),
            BaselineComparisonMetrics(
                name="Naive Concatenation (Raw Union)",
                description=f"Direct union of both sensors ({total_naive} rows) without deduplication, failing to link {matched_pairs_count} co-occurring hotspot detections.",
                total_records=total_naive,
                unique_time_locations=total_naive - matched_pairs_count,
                duplicate_estimate=matched_pairs_count,
            ),
            BaselineComparisonMetrics(
                name="Proposed Harmonisation Model",
                description=f"Linked harmonised product ({len(records)} records: {summary.counts.matched_count} matched, {summary.counts.ambiguous_count} ambiguous, {summary.counts.unmatched_modis_count} unmatched MODIS, {summary.counts.unmatched_viirs_count} unmatched VIIRS).",
                total_records=len(records),
                unique_time_locations=len(records),
                duplicate_estimate=0,
            ),
        ]

        return baselines_list, four_baselines_dict

    @classmethod
    def run_threshold_sensitivity_grid(
        cls,
        modis_obs: List[StandardizedObservationSchema],
        viirs_obs: List[StandardizedObservationSchema],
        base_params: MatchingParameters,
        distance_grid_m: Optional[List[float]] = None,
        time_grid_s: Optional[List[float]] = None,
    ) -> List[SensitivityGridPoint]:
        """
        Execute sensitivity analysis across a matrix of spatial distance and temporal thresholds.
        Default grid: distances = [375, 750, 1000, 1500, 2000]m, times = [900, 1800, 3600, 7200]s.
        """
        dist_grid = distance_grid_m or [375.0, 750.0, 1000.0, 1500.0, 2000.0]
        t_grid = time_grid_s or [900.0, 1800.0, 3600.0, 7200.0]
        points: List[SensitivityGridPoint] = []

        for d_m in dist_grid:
            for t_s in t_grid:
                test_params = MatchingParameters(
                    max_distance_meters=d_m,
                    max_time_difference_seconds=t_s,
                    ambiguity_policy=base_params.ambiguity_policy,
                    matching_method_version=base_params.matching_method_version,
                    quality_filters=base_params.quality_filters,
                    score_weights=base_params.score_weights,
                )
                engine_res = MatchingEngineService.run_harmonisation(
                    run_id=f"sens-{int(d_m)}-{int(t_s)}",
                    modis_observations=modis_obs,
                    viirs_observations=viirs_obs,
                    parameters=test_params,
                )
                summary = engine_res.summary_report
                points.append(
                    SensitivityGridPoint(
                        spatial_threshold_m=d_m,
                        temporal_threshold_s=t_s,
                        matched_count=summary.counts.matched_count,
                        ambiguous_count=summary.counts.ambiguous_count,
                        unmatched_modis_count=summary.counts.unmatched_modis_count,
                        unmatched_viirs_count=summary.counts.unmatched_viirs_count,
                        match_rate=summary.rates.modis_match_rate,
                        viirs_match_rate=summary.rates.viirs_match_rate,
                        ambiguity_rate=summary.rates.ambiguity_rate,
                    )
                )

        return points

    @classmethod
    def generate_evaluation(
        cls,
        summary: ProcessingRunSummary,
        records: List[HarmonisedRecord],
        modis_observations: List[StandardizedObservationSchema],
        viirs_observations: List[StandardizedObservationSchema],
    ) -> RunDetailedEvaluation:
        """
        Generate complete evaluation summary including 4 baselines, sensitivity grid,
        distribution histograms, and FRP percentile comparisons.
        """
        # 1. Four Mandatory Baselines
        baselines_list, four_baselines_dict = cls.compute_four_baselines(
            modis_obs=modis_observations,
            viirs_obs=viirs_observations,
            records=records,
            summary=summary,
        )

        # 2. Threshold Sensitivity Grid
        sensitivity_grid = cls.run_threshold_sensitivity_grid(
            modis_obs=modis_observations,
            viirs_obs=viirs_observations,
            base_params=summary.parameters,
        )

        # 3. Spatial Distance Distribution
        matched_records = [
            r for r in records if r.match_status == MatchStatus.MATCHED and r.spatial_distance_m is not None
        ]
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

        # 4. Time Difference Distribution
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

        # 5. Temporal Hourly Activity Distribution
        hourly_counts: Dict[str, int] = {f"{h:02d}:00 UTC": 0 for h in range(24)}
        for m in modis_observations:
            dt = MatchingEngineService.parse_datetime(m.observation_time_utc)
            if dt:
                hourly_counts[f"{dt.hour:02d}:00 UTC"] += 1
        for v in viirs_observations:
            dt = MatchingEngineService.parse_datetime(v.observation_time_utc)
            if dt:
                hourly_counts[f"{dt.hour:02d}:00 UTC"] += 1

        active_hourly_distribution = [
            DistributionBin(bin=k, count=v) for k, v in hourly_counts.items() if v > 0
        ]

        # 6. FRP Percentiles and Histograms
        m_frp_vals = [m.frp_raw for m in modis_observations if m.frp_raw is not None]
        v_frp_vals = [v.frp_raw for v in viirs_observations if v.frp_raw is not None]

        frp_percentiles = {
            "MODIS": cls.compute_frp_percentiles(m_frp_vals),
            "VIIRS": cls.compute_frp_percentiles(v_frp_vals),
        }

        modis_frp_bins = {name: 0 for name, _, _ in cls.FRP_BINS}
        for val in m_frp_vals:
            for name, low, high in cls.FRP_BINS:
                if low <= val < high or (high == float("inf") and val >= low):
                    modis_frp_bins[name] += 1
                    break

        viirs_frp_bins = {name: 0 for name, _, _ in cls.FRP_BINS}
        for val in v_frp_vals:
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
            baselines=baselines_list,
            sensitivity_grid=sensitivity_grid,
            spatial_distance_distribution=spatial_distribution,
            time_difference_distribution=time_distribution,
            frp_distribution=frp_dist,
            four_baselines=four_baselines_dict,
            frp_percentiles=frp_percentiles,
            temporal_hourly_distribution=active_hourly_distribution,
        )
