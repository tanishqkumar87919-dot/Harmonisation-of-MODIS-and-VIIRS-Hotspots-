"""End-to-End System Integration and Transactional Rollback Tests.

Verifies:
- Transactional rollback on mid-run failure preventing partial outputs
- Error masking preserving database and internal secrets
- 409 Conflict returned when querying incomplete or failed runs
- End-to-end seed demo fixture execution
- Full FastAPI HTTP workflow from dataset upload to run execution and exports
"""

import io
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.api.routes.datasets import obs_model_to_schema
from backend.app.config import settings
from backend.app.db.models import (
    Base,
    DatasetModel,
    HarmonisedRecordModel,
    MatchCandidateModel,
    ObservationModel,
    ProcessingRunModel,
)
from backend.app.db.repositories import (
    DatasetRepository,
    ObservationRepository,
    ProcessingRunRepository,
)
from backend.app.db.session import create_db_engine, get_db, init_db_extensions
from backend.app.main import app
from scripts.seed_demo_fixtures import seed_fixtures


@pytest.fixture
def client_and_db():
    """Create test client with clean in-memory database."""
    test_engine = create_db_engine("sqlite:///:memory:")
    init_db_extensions(test_engine)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client, test_engine

    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)


def test_transactional_rollback_on_mid_run_failure(client_and_db):
    """
    Verify that if an error occurs mid-run:
    1. Transaction rolls back immediately.
    2. Zero partial harmonised_records or match_candidates persist in the database.
    3. ProcessingRunModel is recorded as 'failed' with a sanitized error message.
    4. Subsequent requests for /matches return HTTP 409 Conflict.
    """
    client, engine = client_and_db

    # 1. Ingest MODIS & VIIRS datasets
    with Session(engine) as session:
        modis_uuid = uuid.uuid4()
        viirs_uuid = uuid.uuid4()
        now = datetime.now(timezone.utc)

        m_ds = DatasetModel(
            id=modis_uuid,
            sensor="MODIS",
            product_name="MOD14",
            product_version="C6.1",
            retrieved_at=now,
            metadata_json={"external_id": "modis-rb-test", "total_rows": 1, "valid_rows": 1},
        )
        v_ds = DatasetModel(
            id=viirs_uuid,
            sensor="VIIRS",
            product_name="VNP14IMGTDL",
            product_version="v1.0",
            retrieved_at=now,
            metadata_json={"external_id": "viirs-rb-test", "total_rows": 1, "valid_rows": 1},
        )
        session.add_all([m_ds, v_ds])
        session.flush()

        m_obs = ObservationModel(
            id=uuid.uuid4(),
            dataset_id=modis_uuid,
            source_record_id="m-row-1",
            sensor="MODIS",
            observed_at=now,
            latitude=29.35,
            longitude=76.81,
            confidence_raw="85",
            quality_status="valid",
            raw_fields={},
        )
        v_obs = ObservationModel(
            id=uuid.uuid4(),
            dataset_id=viirs_uuid,
            source_record_id="v-row-1",
            sensor="VIIRS",
            observed_at=now,
            latitude=29.351,
            longitude=76.811,
            confidence_raw="nominal",
            quality_status="valid",
            raw_fields={},
        )
        session.add_all([m_obs, v_obs])
        session.commit()

    # 2. Simulate mid-run failure during matching engine execution
    payload = {
        "modis_dataset_id": "modis-rb-test",
        "viirs_dataset_id": "viirs-rb-test",
        "parameters": {
            "max_distance_meters": 1000.0,
            "max_time_difference_seconds": 1800.0,
            "ambiguity_policy": "retain_ambiguous",
            "matching_method_version": "1.0.0",
            "quality_filters": {"include_warnings": True},
        },
    }

    with patch(
        "backend.app.services.matching_engine.MatchingEngineService.run_harmonisation",
        side_effect=RuntimeError("Simulated mid-run worker crash: password=secret_db_pass!"),
    ):
        res = client.post("/api/runs", json=payload)
        assert res.status_code == 500
        # Verify secret was sanitized and never leaked
        assert "secret_db_pass" not in res.text

    # 3. Verify zero partial harmonised records exist in database
    with Session(engine) as session:
        records_count = session.scalar(sa.select(sa.func.count(HarmonisedRecordModel.id)))
        candidates_count = session.scalar(sa.select(sa.func.count(MatchCandidateModel.id)))
        assert records_count == 0
        assert candidates_count == 0

        # Verify run status is recorded as failed
        failed_run = session.scalar(sa.select(ProcessingRunModel))
        assert failed_run is not None
        assert failed_run.status == "failed"
        assert failed_run.completed_at is not None
        assert "secret_db_pass" not in (failed_run.error_summary or "")
        run_id = str(failed_run.id)

    # 4. Attempting to query matches for failed run must yield HTTP 409 Conflict
    conflict_res = client.get(f"/api/runs/{run_id}/matches")
    assert conflict_res.status_code == 409
    assert "Results are only available for succeeded runs" in conflict_res.json()["detail"]

    # 5. Exporting failed run must also return 409 Conflict
    export_res = client.get(f"/api/runs/{run_id}/export?format=csv")
    assert export_res.status_code == 409


def test_seed_demo_fixtures_script_executes_cleanly():
    """Verify that standalone seed_demo_fixtures CLI function runs end-to-end without errors."""
    result = seed_fixtures()
    assert result is not None
    assert "run_id" in result
    assert result["matched"] == 5
    assert result["unmatched_modis"] == 6
    assert result["unmatched_viirs"] == 7
    assert result["ambiguous"] == 1


def test_end_to_end_api_lifecycle(client_and_db):
    """
    Test complete user workflow via HTTP API:
    Upload MODIS CSV -> Upload VIIRS CSV -> Create Run -> Retrieve Matches -> Export GeoJSON.
    """
    client, _ = client_and_db

    modis_csv = (
        "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight\n"
        "28.50,77.10,320.5,1.0,1.0,2023-05-01,0630,Terra,MODIS,85,6.1N,295.0,25.4,D\n"
        "28.60,77.20,310.2,1.1,1.0,2023-05-01,0630,Terra,MODIS,70,6.1N,290.0,18.2,D\n"
    )
    viirs_csv = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "28.501,77.101,335.0,0.375,0.375,2023-05-01,0635,N,VIIRS,nominal,1.0,298.0,12.0,D\n"
        "28.900,77.900,340.0,0.375,0.375,2023-05-01,0635,N,VIIRS,nominal,1.0,300.0,15.0,D\n"
    )

    # 1. Upload MODIS
    res_m = client.post(
        "/api/datasets/validate",
        files={"file": ("test_modis.csv", io.BytesIO(modis_csv.encode("utf-8")), "text/csv")},
    )
    assert res_m.status_code == 201
    modis_ds_id = res_m.json()["dataset_id"]

    # 2. Upload VIIRS
    res_v = client.post(
        "/api/datasets/validate",
        files={"file": ("test_viirs.csv", io.BytesIO(viirs_csv.encode("utf-8")), "text/csv")},
    )
    assert res_v.status_code == 201
    viirs_ds_id = res_v.json()["dataset_id"]

    # 3. Create run
    run_payload = {
        "modis_dataset_id": modis_ds_id,
        "viirs_dataset_id": viirs_ds_id,
        "parameters": {
            "max_distance_meters": 1000.0,
            "max_time_difference_seconds": 1800.0,
            "ambiguity_policy": "retain_ambiguous",
            "matching_method_version": "1.0.0",
            "quality_filters": {"include_warnings": True},
        },
    }
    run_res = client.post("/api/runs", json=run_payload)
    assert run_res.status_code == 201
    run_data = run_res.json()
    run_id = run_data["run_id"]
    assert run_data["status"] == "succeeded"

    # 4. Fetch matches
    matches_res = client.get(f"/api/runs/{run_id}/matches")
    assert matches_res.status_code == 200
    matches = matches_res.json()
    assert len(matches) >= 1

    # 5. Export GeoJSON
    export_res = client.get(f"/api/runs/{run_id}/export?format=geojson")
    assert export_res.status_code == 200
    assert export_res.headers["content-type"] == "application/geo+json"
    geojson = export_res.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0
