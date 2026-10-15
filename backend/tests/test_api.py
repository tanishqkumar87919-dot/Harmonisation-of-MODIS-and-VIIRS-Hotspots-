"""API integration tests for FastAPI endpoints."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.repository import repo

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


def test_datasets_upload_and_listing(client):
    modis_csv = FIXTURES_DIR / "modis_sample_north_india.csv"
    with open(modis_csv, "rb") as f:
        files = {"file": ("modis.csv", f, "text/csv")}
        res = client.post("/api/datasets/validate", files=files)

    assert res.status_code == 201
    report = res.json()
    assert report["sensor"] == "MODIS"
    assert report["total_input_rows"] == 7

    # List datasets
    list_res = client.get("/api/datasets")
    assert list_res.status_code == 200
    datasets = list_res.json()
    assert any(d["id"] == report["dataset_id"] for d in datasets)


def test_invalid_csv_upload_returns_422(client):
    bad_csv = b"brightness,date,time\n300,2023-05-01,1200\n"
    files = {"file": ("bad.csv", bad_csv, "text/csv")}
    res = client.post("/api/datasets/validate", files=files)
    assert res.status_code == 422


def test_complete_harmonisation_run_workflow(client):
    # 1. Upload MODIS
    modis_csv = FIXTURES_DIR / "modis_sample_north_india.csv"
    with open(modis_csv, "rb") as f:
        res_m = client.post("/api/datasets/validate", files={"file": ("m.csv", f, "text/csv")})
    m_id = res_m.json()["dataset_id"]

    # 2. Upload VIIRS
    viirs_csv = FIXTURES_DIR / "viirs_sample_north_india.csv"
    with open(viirs_csv, "rb") as f:
        res_v = client.post("/api/datasets/validate", files={"file": ("v.csv", f, "text/csv")})
    v_id = res_v.json()["dataset_id"]

    # 3. Create run
    run_payload = {
        "modis_dataset_id": m_id,
        "viirs_dataset_id": v_id,
        "parameters": {
            "max_distance_meters": 1500.0,
            "max_time_difference_seconds": 3600.0,
            "time_window_rule": "absolute",
            "ambiguity_policy": "retain_ambiguous",
            "matching_method_version": "v1.0.0-test",
            "quality_filters": {
                "include_warnings": True,
            },
        },
    }
    run_res = client.post("/api/runs", json=run_payload)
    assert run_res.status_code == 201
    run_summary = run_res.json()
    run_id = run_summary["run_id"]
    assert run_summary["status"] == "succeeded"

    # 4. Get run summary
    get_run_res = client.get(f"/api/runs/{run_id}")
    assert get_run_res.status_code == 200

    # 5. Get matched records
    matches_res = client.get(f"/api/runs/{run_id}/matches")
    assert matches_res.status_code == 200
    matches = matches_res.json()
    assert isinstance(matches, list)

    # 6. Get unmatched records
    unmatched_res = client.get(f"/api/runs/{run_id}/unmatched")
    assert unmatched_res.status_code == 200
    unmatched = unmatched_res.json()
    assert len(unmatched) > 0

    # 7. Get detailed scientific evaluation
    eval_res = client.get(f"/api/runs/{run_id}/summary")
    assert eval_res.status_code == 200
    evaluation = eval_res.json()
    assert len(evaluation["baselines"]) == 4
    assert len(evaluation["sensitivity_grid"]) == 20

    # 8. Export CSV
    csv_res = client.get(f"/api/runs/{run_id}/export?format=csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "harmonisation_id" in csv_res.text

    # 9. Export GeoJSON
    geojson_res = client.get(f"/api/runs/{run_id}/export?format=geojson")
    assert geojson_res.status_code == 200
    assert "geo+json" in geojson_res.headers["content-type"]
    geo_data = geojson_res.json()
    assert geo_data["type"] == "FeatureCollection"
    assert len(geo_data["features"]) > 0
