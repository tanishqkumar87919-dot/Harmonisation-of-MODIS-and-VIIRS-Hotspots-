"""Tests for Database Repositories and Alembic Migrations."""

import importlib
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

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
from backend.app.db.session import create_db_engine, init_db_extensions
from backend.app.schemas.dataset import DatasetRecord
from backend.app.schemas.observation import StandardizedObservation


@pytest.fixture
def db_session():
    """Create test session with clean schema."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db_extensions(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_dataset_repository_crud(db_session: Session):
    """Test DatasetRepository creation, lookup, listing, and deletion."""
    repo = DatasetRepository(db_session)

    ds_record = DatasetRecord(
        id="ds-repo-01",
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        source_uri="test_source.csv",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        checksum="sha256abc123",
        total_rows=1,
        valid_rows=1,
        warning_rows=0,
        rejected_rows=0,
    )
    obs_record = StandardizedObservation(
        observation_id="obs-repo-01",
        dataset_id="ds-repo-01",
        ingestion_run_id="ingest-01",
        source_record_id="row-0",
        source_sensor="MODIS",
        platform="Terra",
        product_name="MOD14",
        product_version="C6.1",
        observation_time_utc="2023-05-01T06:00:00Z",
        latitude=29.35,
        longitude=76.81,
        confidence_raw=90,
        frp_raw=35.0,
        frp_unit="MW",
        row_quality_status="valid",
    )

    created_ds = repo.create(ds_record, [obs_record], raw_bytes=b"sample,csv,data")
    db_session.commit()

    assert created_ds is not None
    assert created_ds.sensor == "MODIS"
    assert created_ds.metadata_json["raw_size_bytes"] == len(b"sample,csv,data")

    # Fetch
    fetched = repo.get("ds-repo-01")
    assert fetched is not None
    assert fetched.product_name == "MOD14"

    # List
    all_ds = repo.list_all()
    assert len(all_ds) >= 1

    # Delete
    deleted = repo.delete("ds-repo-01")
    db_session.commit()
    assert deleted is True
    assert repo.get("ds-repo-01") is None


def test_observation_repository_queries_and_eligibility(db_session: Session):
    """Test ObservationRepository pagination, counts, and quality filtering."""
    ds_repo = DatasetRepository(db_session)
    obs_repo = ObservationRepository(db_session)

    ds = DatasetRecord(
        id="ds-obs-test",
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        source_uri="modis_obs_test.csv",
        checksum="testchecksum123456",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        total_rows=3,
        valid_rows=2,
        warning_rows=1,
        rejected_rows=0,
    )
    observations = [
        StandardizedObservation(
            observation_id="obs-1",
            dataset_id="ds-obs-test",
            ingestion_run_id="ingest-02",
            source_record_id="row-1",
            source_sensor="MODIS",
            platform="Terra",
            product_name="MOD14",
            product_version="C6.1",
            observation_time_utc="2023-05-01T06:00:00Z",
            latitude=29.35,
            longitude=76.81,
            confidence_raw=85,
            row_quality_status="valid",
        ),
        StandardizedObservation(
            observation_id="obs-2",
            dataset_id="ds-obs-test",
            ingestion_run_id="ingest-02",
            source_record_id="row-2",
            source_sensor="MODIS",
            platform="Terra",
            product_name="MOD14",
            product_version="C6.1",
            observation_time_utc="2023-05-01T06:00:00Z",
            latitude=29.36,
            longitude=76.82,
            confidence_raw=25,
            row_quality_status="warning",
            quality_notes=["Low confidence detection"],
        ),
        StandardizedObservation(
            observation_id="obs-3",
            dataset_id="ds-obs-test",
            ingestion_run_id="ingest-02",
            source_record_id="row-3",
            source_sensor="MODIS",
            platform="Terra",
            product_name="MOD14",
            product_version="C6.1",
            observation_time_utc="2023-05-01T06:00:00Z",
            latitude=0.0,
            longitude=0.0,
            row_quality_status="rejected",
            quality_notes=["Low quality detection"],
        ),
    ]

    ds_repo.create(ds, observations)
    db_session.commit()

    assert obs_repo.count_by_dataset("ds-obs-test") == 3
    page1 = obs_repo.get_by_dataset("ds-obs-test", limit=2, offset=0)
    assert len(page1) == 2

    # Eligibility: without warnings
    strict_eligible = obs_repo.get_eligible("ds-obs-test", include_warnings=False)
    assert len(strict_eligible) == 1
    assert strict_eligible[0].quality_status == "valid"

    # Eligibility: with warnings
    with_warnings = obs_repo.get_eligible("ds-obs-test", include_warnings=True)
    assert len(with_warnings) == 2

    # Eligibility: with min confidence threshold
    high_conf = obs_repo.get_eligible("ds-obs-test", include_warnings=True, min_modis_confidence=50)
    assert len(high_conf) == 1


def test_processing_run_repository_lifecycle_and_spatial_candidates(db_session: Session):
    """Test ProcessingRunRepository creation, status update, results saving, and candidate search."""
    ds_repo = DatasetRepository(db_session)
    run_repo = ProcessingRunRepository(db_session)

    # Ingest MODIS observation
    modis_ds = DatasetRecord(
        id="modis-cand-ds",
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        source_uri="modis_sample.csv",
        checksum="modis_checksum",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        total_rows=1,
        valid_rows=1,
        warning_rows=0,
        rejected_rows=0,
    )
    modis_obs = [
        StandardizedObservation(
            observation_id="m-cand-1",
            dataset_id="modis-cand-ds",
            ingestion_run_id="ingest-03",
            source_record_id="m-row-1",
            source_sensor="MODIS",
            platform="Terra",
            product_name="MOD14",
            product_version="C6.1",
            observation_time_utc="2023-05-01T06:00:00Z",
            latitude=29.3500,
            longitude=76.8100,
            confidence_raw=80,
            row_quality_status="valid",
        )
    ]
    m_ds_model = ds_repo.create(modis_ds, modis_obs)

    # Ingest VIIRS observation 200m away, 10s difference
    viirs_ds = DatasetRecord(
        id="viirs-cand-ds",
        sensor="VIIRS",
        product_name="VNP14IMGTDL",
        product_version="v1.0",
        source_uri="viirs_sample.csv",
        checksum="viirs_checksum",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        total_rows=1,
        valid_rows=1,
        warning_rows=0,
        rejected_rows=0,
    )
    viirs_obs = [
        StandardizedObservation(
            observation_id="v-cand-1",
            dataset_id="viirs-cand-ds",
            ingestion_run_id="ingest-03",
            source_record_id="v-row-1",
            source_sensor="VIIRS",
            platform="Suomi-NPP",
            product_name="VNP14IMGTDL",
            product_version="v1.0",
            observation_time_utc="2023-05-01T06:00:10Z",
            latitude=29.3515,
            longitude=76.8115,
            confidence_raw="nominal",
            row_quality_status="valid",
        )
    ]
    v_ds_model = ds_repo.create(viirs_ds, viirs_obs)
    db_session.commit()

    # Find candidates
    candidates = run_repo.find_spatial_temporal_candidates(
        modis_dataset_id=m_ds_model.id,
        viirs_dataset_id=v_ds_model.id,
        max_distance_meters=1000.0,
        max_time_difference_seconds=1800.0,
    )
    assert len(candidates) == 1
    assert candidates[0]["spatial_distance_m"] < 1000.0
    assert candidates[0]["time_difference_s"] == 10.0

    # Create run
    run = ProcessingRunModel(
        started_at=datetime.now(timezone.utc),
        status="running",
        method_version="1.0.0",
        parameters={"max_distance_meters": 1000.0},
        input_dataset_ids={"modis_dataset_id": str(m_ds_model.id), "viirs_dataset_id": str(v_ds_model.id)},
    )
    created_run = run_repo.create(run)
    db_session.commit()

    # Save results
    candidate_model = MatchCandidateModel(
        run_id=created_run.id,
        modis_observation_id=candidates[0]["modis_observation_id"],
        viirs_observation_id=candidates[0]["viirs_observation_id"],
        spatial_distance_m=candidates[0]["spatial_distance_m"],
        time_difference_s=candidates[0]["time_difference_s"],
        decision="accepted",
        decision_reason="Nearest neighbor within thresholds",
    )
    record_model = HarmonisedRecordModel(
        run_id=created_run.id,
        match_status="matched",
        modis_observation_id=candidates[0]["modis_observation_id"],
        viirs_observation_id=candidates[0]["viirs_observation_id"],
        attributes={"harmonised_frp": 30.0},
        provenance={"rule": "1:1 match"},
    )
    run_repo.save_results(
        run_id=created_run.id,
        candidates=[candidate_model],
        records=[record_model],
        summary={"total_records": 1, "matched": 1},
    )
    db_session.commit()

    saved_run = run_repo.get(created_run.id)
    assert saved_run is not None
    assert saved_run.status == "succeeded"
    assert saved_run.completed_at is not None
    assert len(run_repo.get_candidates(created_run.id)) == 1
    assert len(run_repo.get_records(created_run.id, match_status="matched")) == 1


def test_alembic_migration_module_inspectable():
    """Verify Alembic initial schema migration imports and defines upgrade/downgrade hooks."""
    migration = importlib.import_module(
        "backend.app.db.migrations.versions.0001_initial_modis_viirs_schema"
    )
    assert migration.revision == "0001"
    assert migration.down_revision is None
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)
