"""Phase 2 Acceptance & Verification: Ingestion, Validation & Standardization Pipeline."""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.datasets import RowQualityStatus, SensorType
from backend.app.services.ingestion import IngestionError, IngestionService
from backend.app.services.standardization import StandardizationService

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_valid_modis_upload_and_standardization(client):
    csv_path = FIXTURES_DIR / "modis_sample_north_india.csv"
    with open(csv_path, "rb") as f:
        res = client.post(
            "/api/datasets/validate",
            files={"file": ("modis.csv", f, "text/csv")},
            data={"sensor": "MODIS", "product_name": "MOD14", "product_version": "C6.1"},
        )

    assert res.status_code == 201
    report = res.json()
    assert report["sensor"] == "MODIS"
    assert report["product_name"] == "MOD14"
    assert report["total_input_rows"] == 7
    assert report["valid_count"] >= 4
    assert report["duplicate_row_count"] == 1
    assert "duplicate_source_row" in report["rejection_reasons"]

    # Verify retrieval with pagination
    ds_id = report["dataset_id"]
    get_res = client.get(f"/api/datasets/{ds_id}?limit=5")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["dataset"]["id"] == ds_id
    assert len(detail["observations"]) <= 5
    assert detail["total_observations"] == 7


def test_valid_viirs_upload_and_standardization(client):
    csv_path = FIXTURES_DIR / "viirs_sample_north_india.csv"
    with open(csv_path, "rb") as f:
        res = client.post(
            "/api/datasets/validate",
            files={"file": ("viirs.csv", f, "text/csv")},
            data={"sensor": "VIIRS"},
        )

    assert res.status_code == 201
    report = res.json()
    assert report["sensor"] == "VIIRS"
    assert report["total_input_rows"] == 6
    assert report["rejected_count"] == 0
    assert report["valid_count"] == 5
    assert report["warning_count"] == 1  # 1 low confidence


def test_out_of_range_coordinates(client):
    bad_coords_csv = (
        b"latitude,longitude,acq_date,acq_time,confidence,frp,scan,track\n"
        b"95.0,76.5,2023-05-01,0530,85,25.0,1.0,1.0\n"
        b"29.5,-195.0,2023-05-01,0530,85,25.0,1.0,1.0\n"
        b"29.5,76.5,2023-05-01,0530,85,25.0,1.0,1.0\n"
    )
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("bad_coords.csv", bad_coords_csv, "text/csv")},
    )
    assert res.status_code == 201
    report = res.json()
    assert report["total_input_rows"] == 3
    assert report["rejected_count"] == 2
    assert report["valid_count"] == 1
    assert report["out_of_range_coordinate_count"] == 2
    assert "invalid_or_out_of_range_latitude" in report["rejection_reasons"]
    assert "invalid_or_out_of_range_longitude" in report["rejection_reasons"]


def test_malformed_timestamp_2599(client):
    bad_time_csv = (
        b"latitude,longitude,acq_date,acq_time,confidence,scan,track\n"
        b"29.5,76.5,2023-05-01,2599,85,1.0,1.0\n"
        b"29.5,76.5,2023-13-45,1200,85,1.0,1.0\n"
    )
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("bad_time.csv", bad_time_csv, "text/csv")},
    )
    assert res.status_code == 201
    report = res.json()
    assert report["total_input_rows"] == 2
    assert report["rejected_count"] == 2
    assert report["malformed_timestamp_count"] == 2
    assert "malformed_or_missing_timestamp" in report["rejection_reasons"]


def test_duplicate_row_rejection(client):
    dup_csv = (
        b"latitude,longitude,acq_date,acq_time,confidence,frp,scan,track\n"
        b"29.12345,76.54321,2023-05-01,0530,80,20.0,1.0,1.0\n"
        b"29.12345,76.54321,2023-05-01,0530,80,20.0,1.0,1.0\n"
    )
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("dup.csv", dup_csv, "text/csv")},
    )
    assert res.status_code == 201
    report = res.json()
    assert report["total_input_rows"] == 2
    assert report["valid_count"] == 1
    assert report["rejected_count"] == 1
    assert report["duplicate_row_count"] == 1
    assert "duplicate_source_row" in report["rejection_reasons"]


def test_missing_required_columns_raises_422(client):
    missing_cols_csv = b"brightness,confidence,frp\n320.0,85,25.0\n"
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("missing.csv", missing_cols_csv, "text/csv")},
    )
    assert res.status_code == 422
    data = res.json()
    assert "latitude" in str(data["detail"])


def test_empty_file_raises_422(client):
    empty_csv = b""
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("empty.csv", empty_csv, "text/csv")},
    )
    assert res.status_code == 422
