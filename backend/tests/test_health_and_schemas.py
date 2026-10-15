"""Phase 1 Unit & Integration Tests: Health, Config, Schemas, and Error Handling."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.config import settings
from backend.app.main import app
from backend.app.schemas import (
    AmbiguityPolicy,
    DatasetRecord,
    HarmonisedRecord,
    HarmonisedRecordProvenance,
    MatchingParameters,
    MatchingQualityFilters,
    MatchStatus,
    RowQualityStatus,
    SensorType,
    StandardizedObservation,
    ValidationReport,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION
    assert "timestamp" in data
    assert data["database_connected"] is True


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION


def test_config_settings_defaults():
    assert settings.MAX_UPLOAD_SIZE_MB == 50
    assert ".csv" in settings.ALLOWED_EXTENSIONS
    assert settings.APP_VERSION == "1.0.0"
    assert settings.API_V1_PREFIX == "/api"


def test_standardized_observation_17_fields():
    obs = StandardizedObservation(
        observation_id="obs-modis-test-123",
        dataset_id="ds-test-001",
        source_record_id="row-0",
        source_sensor=SensorType.MODIS,
        platform="Terra",
        product_name="MOD14",
        product_version="C6.1",
        observation_time_utc="2023-05-01T05:30:00Z",
        latitude=29.3541,
        longitude=76.8123,
        confidence_raw=85,
        frp_raw=28.4,
        frp_unit="MW",
        scan_raw=1.0,
        track_raw=1.0,
        quality_flags_raw={"daynight": "D"},
        ingestion_run_id="run-ingest-001",
        row_quality_status=RowQualityStatus.VALID,
        quality_notes=[],
        raw_fields={"latitude": 29.3541, "confidence": 85},
    )

    assert obs.observation_id == "obs-modis-test-123"
    assert obs.source_sensor == SensorType.MODIS
    assert obs.latitude == 29.3541
    assert obs.longitude == 76.8123
    assert obs.frp_unit == "MW"
    assert obs.row_quality_status == RowQualityStatus.VALID


def test_observation_coordinate_bounds_validation():
    with pytest.raises(ValidationError):
        StandardizedObservation(
            observation_id="bad-lat",
            dataset_id="ds-1",
            source_record_id="1",
            source_sensor=SensorType.MODIS,
            platform="Terra",
            product_name="MOD14",
            product_version="C6.1",
            observation_time_utc="2023-05-01T05:30:00Z",
            latitude=95.0,  # Invalid: > 90.0
            longitude=76.0,
            ingestion_run_id="ingest-1",
        )


def test_matching_parameters_validation():
    params = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.RETAIN_AMBIGUOUS,
    )
    assert params.max_distance_meters == 1500.0
    assert params.ambiguity_policy == AmbiguityPolicy.RETAIN_AMBIGUOUS

    # Distance must be > 0
    with pytest.raises(ValidationError):
        MatchingParameters(max_distance_meters=-10.0)


def test_structured_error_handling_404(client):
    res = client.get("/api/runs/nonexistent-run-id-9999")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert "detail" in data
    assert data["status_code"] == 404
    assert "remediation" in data


def test_structured_error_handling_422(client):
    # Missing required fields in POST /api/runs
    res = client.post("/api/runs", json={})
    assert res.status_code == 422
    data = res.json()
    assert data["error"] == "Request Schema Validation Failed"
    assert data["status_code"] == 422
    assert "remediation" in data
