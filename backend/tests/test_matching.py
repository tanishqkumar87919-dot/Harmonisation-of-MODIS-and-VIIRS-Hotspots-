"""Unit tests for Phase 4: Matching engine and ambiguity policies."""

from pathlib import Path
import pytest
from backend.app.schemas.common import AmbiguityPolicy, MatchStatus
from backend.app.schemas.matching import MatchingParameters
from backend.app.services.ingestion import IngestionService
from backend.app.services.matching import MatchingEngine
from backend.app.services.standardization import StandardizationService


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


@pytest.fixture
def sample_observations():
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

    return m_eligible, v_eligible


def test_haversine_distance():
    # 29.3541, 76.8123 and 29.3550, 76.8130 are ~120m apart
    dist = MatchingEngine.haversine_distance_meters(29.3541, 76.8123, 29.3550, 76.8130)
    assert 100.0 < dist < 150.0


def test_matching_retain_ambiguous(sample_observations):
    m_obs, v_obs = sample_observations

    params = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.RETAIN_AMBIGUOUS,
    )

    records, candidates, summary = MatchingEngine.execute_matching_run(
        run_id="run-test-ambiguous",
        modis_observations=m_obs,
        viirs_observations=v_obs,
        parameters=params,
    )

    assert len(candidates) > 0
    assert summary.counts.matched_count > 0 or summary.counts.ambiguous_count > 0
    # Check that unmatched records are preserved!
    assert summary.counts.unmatched_modis_count > 0
    assert summary.counts.unmatched_viirs_count > 0

    # Ensure every harmonised record has provenance
    for rec in records:
        assert rec.provenance is not None
        assert rec.run_id == "run-test-ambiguous"
        assert rec.matching_method_version == params.matching_method_version


def test_matching_one_to_one_deterministic(sample_observations):
    m_obs, v_obs = sample_observations

    params = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.ONE_TO_ONE_DETERMINISTIC,
    )

    records, candidates, summary = MatchingEngine.execute_matching_run(
        run_id="run-test-deterministic",
        modis_observations=m_obs,
        viirs_observations=v_obs,
        parameters=params,
    )

    # In deterministic 1:1, there are 0 ambiguous records
    assert summary.counts.ambiguous_count == 0
    assert summary.counts.matched_count > 0

    # Check 1:1 exclusivity among matched records
    matched_m_ids = [r.modis_observation_id for r in records if r.match_status == MatchStatus.MATCHED]
    matched_v_ids = [r.viirs_observation_id for r in records if r.match_status == MatchStatus.MATCHED]
    assert len(matched_m_ids) == len(set(matched_m_ids))
    assert len(matched_v_ids) == len(set(matched_v_ids))


def test_matching_many_to_many(sample_observations):
    m_obs, v_obs = sample_observations

    params = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.MANY_TO_MANY,
    )

    records, candidates, summary = MatchingEngine.execute_matching_run(
        run_id="run-test-m2m",
        modis_observations=m_obs,
        viirs_observations=v_obs,
        parameters=params,
    )

    assert summary.counts.matched_count == len(candidates)
