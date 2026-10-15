"""Unit tests for Phase 5: Scientific evaluation and sensitivity analysis."""

from pathlib import Path
import pytest
from backend.app.schemas.matching import MatchingParameters
from backend.app.services.evaluation import EvaluationService
from backend.app.services.ingestion import IngestionService
from backend.app.services.matching import MatchingEngine
from backend.app.services.standardization import StandardizationService


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


def test_detailed_evaluation_generation():
    modis_csv = FIXTURES_DIR / "modis_sample_north_india.csv"
    viirs_csv = FIXTURES_DIR / "viirs_sample_north_india.csv"

    with open(modis_csv, "rb") as f:
        _, m_ds, m_df = IngestionService.inspect_and_validate(f.read(), source_uri="modis.csv")
    with open(viirs_csv, "rb") as f:
        _, v_ds, v_df = IngestionService.inspect_and_validate(f.read(), source_uri="viirs.csv")

    m_obs = StandardizationService.standardize_records(m_df, m_ds)
    v_obs = StandardizationService.standardize_records(v_df, v_ds)

    m_eligible = StandardizationService.get_eligible_observations(m_obs)
    v_eligible = StandardizationService.get_eligible_observations(v_obs)

    params = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
    )

    records, candidates, summary = MatchingEngine.execute_matching_run(
        run_id="run-eval-test",
        modis_observations=m_eligible,
        viirs_observations=v_eligible,
        parameters=params,
    )

    evaluation = EvaluationService.generate_evaluation(
        summary=summary,
        records=records,
        modis_observations=m_eligible,
        viirs_observations=v_eligible,
    )

    assert evaluation.run_id == "run-eval-test"

    # 1. Baseline comparisons
    assert len(evaluation.baselines) == 4
    naive_baseline = next(b for b in evaluation.baselines if "Naive" in b.name)
    assert naive_baseline.total_records == len(m_eligible) + len(v_eligible)

    # 2. Sensitivity grid
    assert len(evaluation.sensitivity_grid) == 20  # 5 spatial x 4 temporal thresholds
    for pt in evaluation.sensitivity_grid:
        assert pt.spatial_threshold_m > 0
        assert pt.temporal_threshold_s > 0
        assert 0.0 <= pt.match_rate <= 100.0

    # 3. Spatial and temporal distributions
    assert len(evaluation.spatial_distance_distribution) == 5
    assert len(evaluation.time_difference_distribution) == 5

    # 4. FRP distributions & disclaimer
    assert evaluation.frp_distribution is not None
    assert len(evaluation.frp_distribution.modis_frp) == 5
    assert len(evaluation.frp_distribution.viirs_frp) == 5
    assert "not be averaged" in evaluation.frp_distribution.scientific_disclaimer.lower()
