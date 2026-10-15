"""Tests for Core Source ORM Models (datasets and observations).

Verifies:
- Table creation and schema definitions
- Insertion of valid, warning, and rejected observations
- Check constraints blocking invalid latitudes, longitudes, sensors, and NULL timestamps
- Permissive handling for rejected records with NULL timestamps and coordinates
- Raw source field immutability enforcement
- Foreign key and cascade relationships
"""

import uuid
from datetime import datetime, timezone
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.app.db.models import Base, DatasetModel, ObservationModel
from backend.app.db.session import create_db_engine, init_db_extensions


@pytest.fixture
def db_session():
    """Create an isolated in-memory test database session."""
    test_engine = create_db_engine("sqlite:///:memory:")
    init_db_extensions(test_engine)
    Base.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        yield session

    Base.metadata.drop_all(test_engine)


def test_insert_valid_and_warning_observations(db_session: Session):
    """Verify standard valid and warning records can be inserted with auto-generated geometry."""
    dataset = DatasetModel(
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        source_uri="MOD14_2023_test.csv",
        retrieved_at=datetime.now(timezone.utc),
        checksum="testchecksum1234567890",
        metadata_json={"rows_imported": 2},
    )
    db_session.add(dataset)
    db_session.commit()

    valid_obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-001",
        sensor="MODIS",
        observed_at=datetime.now(timezone.utc),
        latitude=28.6139,
        longitude=77.2090,
        confidence_raw="85",
        frp_raw=32.4,
        frp_unit="MW",
        raw_fields={"brightness": 320.5, "scan": 1.1},
        quality_status="valid",
        quality_notes=[],
    )
    db_session.add(valid_obs)

    warning_obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-002",
        sensor="MODIS",
        observed_at=datetime.now(timezone.utc),
        latitude=28.7041,
        longitude=77.1025,
        confidence_raw="20",
        frp_raw=5.2,
        frp_unit="MW",
        raw_fields={"brightness": 305.1},
        quality_status="warning",
        quality_notes=["Low confidence detection (20)"],
    )
    db_session.add(warning_obs)
    db_session.commit()

    # Verify retrieval and auto-populated geom
    retrieved_valid = db_session.get(ObservationModel, valid_obs.id)
    assert retrieved_valid is not None
    assert retrieved_valid.sensor == "MODIS"
    assert retrieved_valid.quality_status == "valid"
    assert retrieved_valid.geom is not None
    assert "POINT(77.209 28.6139)" in str(retrieved_valid.geom)
    assert retrieved_valid.dataset.product_name == "MOD14"

    retrieved_warning = db_session.get(ObservationModel, warning_obs.id)
    assert retrieved_warning is not None
    assert retrieved_warning.quality_status == "warning"


def test_insert_rejected_observation_with_null_coords_and_time(db_session: Session):
    """Verify rejected records can store NULL observed_at and coordinates for triage."""
    dataset = DatasetModel(
        sensor="VIIRS",
        product_name="VNP14IMGTDL",
        product_version="v1.0",
        retrieved_at=datetime.now(timezone.utc),
        metadata_json={},
    )
    db_session.add(dataset)
    db_session.commit()

    rejected_obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-corrupt-999",
        sensor="VIIRS",
        observed_at=None,
        latitude=None,
        longitude=None,
        geom=None,
        confidence_raw=None,
        frp_raw=None,
        raw_fields={"raw_line": "corrupted,unparseable,record"},
        quality_status="rejected",
        quality_notes=["Malformed timestamp: 2599-99-99", "Coordinate missing"],
    )
    db_session.add(rejected_obs)
    db_session.commit()

    record = db_session.get(ObservationModel, rejected_obs.id)
    assert record is not None
    assert record.quality_status == "rejected"
    assert record.observed_at is None
    assert record.latitude is None
    assert record.geom is None


def test_check_constraint_blocks_invalid_latitude(db_session: Session):
    """ck_observations_latitude_range must block latitude > 90.0 for non-rejected records."""
    dataset = DatasetModel(
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        retrieved_at=datetime.now(timezone.utc),
    )
    db_session.add(dataset)
    db_session.commit()

    invalid_lat_obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-bad-lat",
        sensor="MODIS",
        observed_at=datetime.now(timezone.utc),
        latitude=95.0,  # Invalid: > 90.0
        longitude=77.0,
        quality_status="valid",
        raw_fields={},
        quality_notes=[],
    )
    db_session.add(invalid_lat_obs)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_constraint_blocks_invalid_longitude(db_session: Session):
    """ck_observations_longitude_range must block longitude < -180.0 for non-rejected records."""
    dataset = DatasetModel(
        sensor="VIIRS",
        product_name="VNP14IMGTDL",
        product_version="v1.0",
        retrieved_at=datetime.now(timezone.utc),
    )
    db_session.add(dataset)
    db_session.commit()

    invalid_lon_obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-bad-lon",
        sensor="VIIRS",
        observed_at=datetime.now(timezone.utc),
        latitude=25.0,
        longitude=-195.0,  # Invalid: < -180.0
        quality_status="valid",
        raw_fields={},
        quality_notes=[],
    )
    db_session.add(invalid_lon_obs)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_constraint_blocks_null_observed_at_on_valid(db_session: Session):
    """ck_observations_valid_observed_at must block NULL observed_at when quality_status != 'rejected'."""
    dataset = DatasetModel(
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        retrieved_at=datetime.now(timezone.utc),
    )
    db_session.add(dataset)
    db_session.commit()

    null_time_obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-null-time",
        sensor="MODIS",
        observed_at=None,  # Not allowed for valid
        latitude=25.0,
        longitude=75.0,
        quality_status="valid",
        raw_fields={},
        quality_notes=[],
    )
    db_session.add(null_time_obs)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_constraint_blocks_invalid_sensor(db_session: Session):
    """ck_datasets_sensor and ck_observations_sensor must block unsupported sensors."""
    bad_ds = DatasetModel(
        sensor="GOES",  # Not in ('MODIS', 'VIIRS')
        product_name="ABI",
        product_version="v1",
        retrieved_at=datetime.now(timezone.utc),
    )
    db_session.add(bad_ds)
    with pytest.raises(sa.exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_raw_fields_immutability(db_session: Session):
    """Verify that attempting to overwrite raw observation source fields raises ValueError."""
    dataset = DatasetModel(
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        retrieved_at=datetime.now(timezone.utc),
    )
    db_session.add(dataset)
    db_session.commit()

    obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-immutable-1",
        sensor="MODIS",
        observed_at=datetime.now(timezone.utc),
        latitude=28.0,
        longitude=77.0,
        confidence_raw="90",
        frp_raw=45.0,
        frp_unit="MW",
        raw_fields={"brightness": 325.0, "scan": 1.0},
        quality_status="valid",
    )
    db_session.add(obs)
    db_session.commit()

    # Attempting to mutate raw_fields must be blocked
    obs.raw_fields = {"brightness": 999.9}
    with pytest.raises(ValueError, match="immutable and cannot be overwritten"):
        db_session.commit()
    db_session.rollback()

    # Attempting to mutate confidence_raw must be blocked
    obs.confidence_raw = "10"
    with pytest.raises(ValueError, match="immutable and cannot be overwritten"):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_dataset_deletes_observations(db_session: Session):
    """Deleting a dataset must cascade delete to all child observations."""
    dataset = DatasetModel(
        sensor="MODIS",
        product_name="MOD14",
        product_version="C6.1",
        retrieved_at=datetime.now(timezone.utc),
    )
    db_session.add(dataset)
    db_session.commit()

    obs = ObservationModel(
        dataset_id=dataset.id,
        source_record_id="row-cascade",
        sensor="MODIS",
        observed_at=datetime.now(timezone.utc),
        latitude=28.0,
        longitude=77.0,
        quality_status="valid",
        raw_fields={},
    )
    db_session.add(obs)
    db_session.commit()

    obs_id = obs.id
    db_session.delete(dataset)
    db_session.commit()

    assert db_session.get(ObservationModel, obs_id) is None
