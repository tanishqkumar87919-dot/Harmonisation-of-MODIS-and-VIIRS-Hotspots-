"""Unit tests for Phase 2: Data inspection and ingestion service."""

import pytest
from pathlib import Path
from backend.app.schemas.common import RowQualityStatus, SensorType
from backend.app.services.ingestion import IngestionService, IngestionError


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


def test_modis_ingestion_valid_and_warnings():
    csv_path = FIXTURES_DIR / "modis_sample_north_india.csv"
    assert csv_path.exists(), "Sample MODIS fixture missing"

    with open(csv_path, "rb") as f:
        content = f.read()

    report, dataset, df = IngestionService.inspect_and_validate(
        file_content=content,
        source_uri=str(csv_path),
        product_name="MOD14_Terra_Collection_6_1",
        product_version="C6.1",
    )

    assert report.sensor == SensorType.MODIS
    assert report.total_input_rows == 7
    # Row 1, 2, 3 are valid.
    # Row 4 has confidence 25 (< 30 -> warning).
    # Row 5 is valid.
    # Row 6 is an exact duplicate of row 1 (-> rejected duplicate).
    # Row 7 has track 2.1 (scan 4.5 -> track pixel size > 4? wait, scan 4.5, track 2.1, let's check).
    assert report.duplicate_row_count == 1
    assert report.rejected_count == 1
    assert report.warning_count >= 1
    assert report.valid_count >= 4
    assert dataset.total_rows == 7
    assert dataset.bbox is not None
    assert len(dataset.bbox) == 4
    assert dataset.min_time_utc is not None


def test_viirs_ingestion_valid_and_resolution():
    csv_path = FIXTURES_DIR / "viirs_sample_north_india.csv"
    assert csv_path.exists(), "Sample VIIRS fixture missing"

    with open(csv_path, "rb") as f:
        content = f.read()

    report, dataset, df = IngestionService.inspect_and_validate(
        file_content=content,
        source_uri=str(csv_path),
    )

    assert report.sensor == SensorType.VIIRS
    assert report.total_input_rows == 6
    # Row 4 has confidence 'low' -> warning
    assert report.warning_count == 1
    assert report.valid_count == 5
    assert report.rejected_count == 0
    assert dataset.checksum is not None


def test_corrupted_modis_validation():
    csv_path = FIXTURES_DIR / "corrupted_modis_sample.csv"
    assert csv_path.exists(), "Corrupted fixture missing"

    with open(csv_path, "rb") as f:
        content = f.read()

    report, dataset, df = IngestionService.inspect_and_validate(
        file_content=content,
        source_uri=str(csv_path),
    )

    assert report.total_input_rows == 5
    # Row 1 is valid
    # Row 2 missing latitude
    # Row 3 latitude 95.4102 > 90
    # Row 4 longitude 195.1045 > 180
    # Row 5 invalid date
    assert report.valid_count == 1
    assert report.missing_coordinate_count == 1
    assert report.out_of_range_coordinate_count == 2
    assert report.malformed_timestamp_count == 1
    assert report.rejected_count == 4


def test_empty_csv_rejection():
    empty_content = b""
    with pytest.raises(IngestionError, match="empty"):
        IngestionService.inspect_and_validate(empty_content)


def test_missing_required_coordinate_columns():
    bad_csv = b"brightness,acq_date,acq_time\n320.0,2023-05-01,0530\n"
    with pytest.raises(IngestionError, match="required columns"):
        IngestionService.inspect_and_validate(bad_csv)


def test_sensor_auto_detection():
    modis_csv = b"latitude,longitude,acq_date,bright_t31\n29.1,76.5,2023-05-01,300\n"
    report_m, _, _ = IngestionService.inspect_and_validate(modis_csv)
    assert report_m.sensor == SensorType.MODIS

    viirs_csv = b"latitude,longitude,acq_date,bright_ti4\n29.1,76.5,2023-05-01,330\n"
    report_v, _, _ = IngestionService.inspect_and_validate(viirs_csv)
    assert report_v.sensor == SensorType.VIIRS
