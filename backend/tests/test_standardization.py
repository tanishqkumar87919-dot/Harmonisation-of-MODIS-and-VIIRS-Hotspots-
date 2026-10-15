"""Unit tests for Phase 3: Standardization service."""

from pathlib import Path
import pytest
from backend.app.schemas.common import RowQualityStatus, SensorType
from backend.app.services.ingestion import IngestionService
from backend.app.services.standardization import StandardizationService


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


def test_modis_standardization():
    csv_path = FIXTURES_DIR / "modis_sample_north_india.csv"
    with open(csv_path, "rb") as f:
        content = f.read()

    _, dataset, df = IngestionService.inspect_and_validate(
        file_content=content,
        source_uri=str(csv_path),
    )

    observations = StandardizationService.standardize_records(df, dataset)

    assert len(observations) == 7
    obs = observations[0]

    # Verify 17 internal fields
    assert obs.observation_id.startswith("obs-modis-")
    assert obs.dataset_id == dataset.id
    assert obs.source_sensor == SensorType.MODIS
    assert obs.platform == "Terra"
    assert obs.latitude == 29.3541
    assert obs.longitude == 76.8123
    assert obs.observation_time_utc.startswith("2023-05-01T05:30:00")
    assert obs.confidence_raw == 85.0
    assert obs.frp_raw == 28.4
    assert obs.frp_unit == "MW"
    assert obs.scan_raw == 1.0
    assert obs.track_raw == 1.0
    assert "daynight" in obs.quality_flags_raw
    assert obs.row_quality_status == RowQualityStatus.VALID
    assert "brightness" in obs.raw_fields


def test_viirs_standardization():
    csv_path = FIXTURES_DIR / "viirs_sample_north_india.csv"
    with open(csv_path, "rb") as f:
        content = f.read()

    _, dataset, df = IngestionService.inspect_and_validate(
        file_content=content,
        source_uri=str(csv_path),
    )

    observations = StandardizationService.standardize_records(df, dataset)

    assert len(observations) == 6
    obs = observations[0]

    assert obs.source_sensor == SensorType.VIIRS
    assert obs.platform == "Suomi-NPP"
    assert obs.latitude == 29.3550
    assert obs.longitude == 76.8130
    assert obs.confidence_raw == "nominal"
    assert obs.frp_raw == 14.2
    assert obs.frp_unit == "MW"


def test_eligibility_filtering():
    csv_path = FIXTURES_DIR / "modis_sample_north_india.csv"
    with open(csv_path, "rb") as f:
        content = f.read()

    _, dataset, df = IngestionService.inspect_and_validate(
        file_content=content,
        source_uri=str(csv_path),
    )

    observations = StandardizationService.standardize_records(df, dataset)

    # 1. Total rows = 7 (1 rejected duplicate, 1 warning confidence 25%, 5 valid)
    # Filter with include_warnings=True (default)
    eligible = StandardizationService.get_eligible_observations(observations, include_warnings=True)
    assert len(eligible) == 6  # 5 valid + 1 warning

    # Filter with include_warnings=False
    eligible_no_warn = StandardizationService.get_eligible_observations(observations, include_warnings=False)
    assert len(eligible_no_warn) == 5

    # Filter with min_modis_confidence = 80
    eligible_high_conf = StandardizationService.get_eligible_observations(
        observations, min_modis_confidence=80.0
    )
    # Rows with conf 85, 92, 80 = 3 rows
    assert len(eligible_high_conf) == 3


def test_viirs_confidence_level_filtering():
    csv_path = FIXTURES_DIR / "viirs_sample_north_india.csv"
    with open(csv_path, "rb") as f:
        content = f.read()

    _, dataset, df = IngestionService.inspect_and_validate(
        file_content=content,
        source_uri=str(csv_path),
    )

    observations = StandardizationService.standardize_records(df, dataset)

    # VIIRS sample has 1 'low', 3 'nominal', 2 'high'
    eligible_nominal_high = StandardizationService.get_eligible_observations(
        observations, allowed_viirs_confidence_levels=["nominal", "high"]
    )
    assert len(eligible_nominal_high) == 5
    assert not any(obs.confidence_raw == "low" for obs in eligible_nominal_high)
