"""Tests for Harmonisation ORM Models (processing_runs, match_candidates, and harmonised_records).

Verifies:
- Foreign-key integrity and prevention of orphaned observations
- Cascade deletion when processing_runs are deleted
- Check constraints on processing_runs status
- Non-negative distance and time constraints on match_candidates
- Source link integrity check constraints on harmonised_records (07_DATABASE_SCHEMA.md)
"""

import uuid
from datetime import datetime, timezone
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.app.db.models import (
    Base,
    DatasetModel,
    HarmonisedRecordModel,
    MatchCandidateModel,
    ObservationModel,
    ProcessingRunModel,
)
from backend.app.db.session import create_db_engine, init_db_extensions


@pytest.fixture
def db_session():
    """Isolated in-memory database session."""
    test_engine = create_db_engine("sqlite:///:memory:")
    init_db_extensions(test_engine)
    Base.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        yield session

    Base.metadata.drop_all(test_engine)


@pytest.fixture
def sample_setup(db_session: Session):
    """Seed sample MODIS dataset, VIIRS dataset, and two observations."""
    modis_ds = DatasetModel(
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        retrieved_at=datetime.now(timezone.utc),
    )
    viirs_ds = DatasetModel(
        sensor="VIIRS",
        product_name="VNP14IMGTDL",
        product_version="v1.0",
        retrieved_at=datetime.now(timezone.utc),
    )
    db_session.add_all([modis_ds, viirs_ds])
    db_session.commit()

    now = datetime.now(timezone.utc)
    modis_obs = ObservationModel(
        dataset_id=modis_ds.id,
        source_record_id="modis-01",
        sensor="MODIS",
        observed_at=now,
        latitude=29.35,
        longitude=76.81,
        quality_status="valid",
        raw_fields={"confidence": 85},
    )
    viirs_obs = ObservationModel(
        dataset_id=viirs_ds.id,
        source_record_id="viirs-01",
        sensor="VIIRS",
        observed_at=now,
        latitude=29.351,
        longitude=76.812,
        quality_status="valid",
        raw_fields={"confidence": "nominal"},
    )
    db_session.add_all([modis_obs, viirs_obs])
    db_session.commit()

    run = ProcessingRunModel(
        started_at=now,
        status="running",
        method_version="1.0.0",
        parameters={"max_distance_meters": 1000, "max_time_difference_seconds": 1800},
        input_dataset_ids={"modis_dataset_id": str(modis_ds.id), "viirs_dataset_id": str(viirs_ds.id)},
    )
    db_session.add(run)
    db_session.commit()

    return {
        "modis_ds": modis_ds,
        "viirs_ds": viirs_ds,
        "modis_obs": modis_obs,
        "viirs_obs": viirs_obs,
        "run": run,
    }


def test_insert_valid_match_candidate_and_harmonised_record(db_session: Session, sample_setup):
    """Verify valid match candidates and harmonised records link to runs and observations."""
    run = sample_setup["run"]
    modis_obs = sample_setup["modis_obs"]
    viirs_obs = sample_setup["viirs_obs"]

    candidate = MatchCandidateModel(
        run_id=run.id,
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
        spatial_distance_m=152.3,
        time_difference_s=12.0,
        score=0.95,
        decision="accepted",
        decision_reason="Within 1000m and 1800s mutual nearest-neighbour",
    )
    db_session.add(candidate)

    record = HarmonisedRecordModel(
        run_id=run.id,
        match_status="matched",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
        attributes={"combined_frp": 42.5},
        provenance={"modis_source_id": modis_obs.source_record_id, "viirs_source_id": viirs_obs.source_record_id},
    )
    db_session.add(record)
    db_session.commit()

    # Query back
    saved_cand = db_session.get(MatchCandidateModel, candidate.id)
    assert saved_cand is not None
    assert saved_cand.decision == "accepted"
    assert saved_cand.modis_observation.source_record_id == "modis-01"

    saved_rec = db_session.get(HarmonisedRecordModel, record.id)
    assert saved_rec is not None
    assert saved_rec.match_status == "matched"
    assert saved_rec.modis_observation_id == modis_obs.id
    assert saved_rec.viirs_observation_id == viirs_obs.id


def test_foreign_key_restricts_deleting_referenced_observation(db_session: Session, sample_setup):
    """Foreign key ondelete='RESTRICT' must prevent deleting observation referenced by harmonised_records."""
    run = sample_setup["run"]
    modis_obs = sample_setup["modis_obs"]
    viirs_obs = sample_setup["viirs_obs"]

    record = HarmonisedRecordModel(
        run_id=run.id,
        match_status="matched",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
        attributes={},
        provenance={},
    )
    db_session.add(record)
    db_session.commit()

    # Attempting to delete modis_obs must fail because it's referenced with RESTRICT
    db_session.delete(modis_obs)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_run_removes_candidates_and_records(db_session: Session, sample_setup):
    """Deleting a processing_run must cascade delete its match_candidates and harmonised_records."""
    run = sample_setup["run"]
    modis_obs = sample_setup["modis_obs"]
    viirs_obs = sample_setup["viirs_obs"]

    candidate = MatchCandidateModel(
        run_id=run.id,
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
        spatial_distance_m=100.0,
        time_difference_s=0.0,
        decision="accepted",
        decision_reason="rule",
    )
    record = HarmonisedRecordModel(
        run_id=run.id,
        match_status="matched",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
        attributes={},
        provenance={},
    )
    db_session.add_all([candidate, record])
    db_session.commit()

    cand_id = candidate.id
    rec_id = record.id

    db_session.delete(run)
    db_session.commit()

    assert db_session.get(MatchCandidateModel, cand_id) is None
    assert db_session.get(HarmonisedRecordModel, rec_id) is None
    # Source observations must remain intact
    assert db_session.get(ObservationModel, modis_obs.id) is not None
    assert db_session.get(ObservationModel, viirs_obs.id) is not None


def test_check_constraint_processing_runs_status(db_session: Session):
    """ck_processing_runs_status must only allow ('queued', 'running', 'succeeded', 'failed')."""
    bad_run = ProcessingRunModel(
        started_at=datetime.now(timezone.utc),
        status="invalid_status",
        method_version="1.0.0",
        parameters={},
        input_dataset_ids={},
    )
    db_session.add(bad_run)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_constraints_match_candidates_nonnegative(db_session: Session, sample_setup):
    """Check constraints must reject negative spatial distance or negative time difference."""
    run = sample_setup["run"]
    modis_obs = sample_setup["modis_obs"]
    viirs_obs = sample_setup["viirs_obs"]

    # Negative distance
    bad_dist = MatchCandidateModel(
        run_id=run.id,
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
        spatial_distance_m=-10.0,
        time_difference_s=10.0,
        decision="rejected",
        decision_reason="test",
    )
    db_session.add(bad_dist)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Negative time
    bad_time = MatchCandidateModel(
        run_id=run.id,
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
        spatial_distance_m=10.0,
        time_difference_s=-5.0,
        decision="rejected",
        decision_reason="test",
    )
    db_session.add(bad_time)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_harmonised_records_source_link_constraints(db_session: Session, sample_setup):
    """
    Verify ck_harmonised_records_source_links rejects invalid status/observation combinations:
    - 'matched' requires both MODIS and VIIRS IDs
    - 'unmatched_modis' requires MODIS ID and NULL VIIRS ID
    - 'unmatched_viirs' requires VIIRS ID and NULL MODIS ID
    - 'ambiguous' requires at least one ID
    """
    run = sample_setup["run"]
    modis_obs = sample_setup["modis_obs"]
    viirs_obs = sample_setup["viirs_obs"]

    # 1. Invalid: matched with missing VIIRS ID
    bad_matched = HarmonisedRecordModel(
        run_id=run.id,
        match_status="matched",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=None,
    )
    db_session.add(bad_matched)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. Invalid: unmatched_modis with VIIRS ID present
    bad_unmatched_modis = HarmonisedRecordModel(
        run_id=run.id,
        match_status="unmatched_modis",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
    )
    db_session.add(bad_unmatched_modis)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Invalid: unmatched_viirs with MODIS ID present
    bad_unmatched_viirs = HarmonisedRecordModel(
        run_id=run.id,
        match_status="unmatched_viirs",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
    )
    db_session.add(bad_unmatched_viirs)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 4. Invalid: ambiguous with neither observation ID present
    bad_ambiguous = HarmonisedRecordModel(
        run_id=run.id,
        match_status="ambiguous",
        modis_observation_id=None,
        viirs_observation_id=None,
    )
    db_session.add(bad_ambiguous)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 5. Valid: unmatched_modis with only MODIS ID
    valid_unmatched_modis = HarmonisedRecordModel(
        run_id=run.id,
        match_status="unmatched_modis",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=None,
    )
    db_session.add(valid_unmatched_modis)

    # 6. Valid: unmatched_viirs with only VIIRS ID
    valid_unmatched_viirs = HarmonisedRecordModel(
        run_id=run.id,
        match_status="unmatched_viirs",
        modis_observation_id=None,
        viirs_observation_id=viirs_obs.id,
    )
    db_session.add(valid_unmatched_viirs)

    # 7. Valid: ambiguous with one or both IDs
    valid_ambiguous = HarmonisedRecordModel(
        run_id=run.id,
        match_status="ambiguous",
        modis_observation_id=modis_obs.id,
        viirs_observation_id=viirs_obs.id,
    )
    db_session.add(valid_ambiguous)

    db_session.commit()
    assert db_session.get(HarmonisedRecordModel, valid_unmatched_modis.id) is not None
    assert db_session.get(HarmonisedRecordModel, valid_unmatched_viirs.id) is not None
    assert db_session.get(HarmonisedRecordModel, valid_ambiguous.id) is not None
