"""Phase 4 Acceptance & Verification: Runs, Evaluation, Sensitivity & Exports."""

import io
import json
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.common import AmbiguityPolicy, MatchStatus, SensorType
from backend.app.schemas.matching import MatchingParameters, RunCreateRequest
from backend.app.services.ingestion import IngestionService
from backend.app.services.repository import repo
from backend.app.services.standardization import StandardizationService

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def run_id(client):
    """Seed MODIS and VIIRS and execute a processing run."""
    modis_csv = FIXTURES_DIR / "modis_sample_north_india.csv"
    viirs_csv = FIXTURES_DIR / "viirs_sample_north_india.csv"

    with open(modis_csv, "rb") as f:
        res_m = client.post("/api/datasets/validate", files={"file": ("modis.csv", f, "text/csv")})
    m_id = res_m.json()["dataset_id"]

    with open(viirs_csv, "rb") as f:
        res_v = client.post("/api/datasets/validate", files={"file": ("viirs.csv", f, "text/csv")})
    v_id = res_v.json()["dataset_id"]

    run_payload = {
        "modis_dataset_id": m_id,
        "viirs_dataset_id": v_id,
        "parameters": {
            "max_distance_meters": 1500.0,
            "max_time_difference_seconds": 3600.0,
            "time_window_rule": "absolute",
            "ambiguity_policy": "retain_ambiguous",
            "matching_method_version": "v1.0.0-phase4",
            "quality_filters": {"include_warnings": True},
        },
    }

    res_run = client.post("/api/runs", json=run_payload)
    assert res_run.status_code == 201
    return res_run.json()["run_id"]


def test_runs_lifecycle_and_matches_filtering(client, run_id):
    # 1. Get run summary
    res_run = client.get(f"/api/runs/{run_id}")
    assert res_run.status_code == 200
    summary = res_run.json()
    assert summary["run_id"] == run_id
    assert summary["status"] == "succeeded"

    # 2. Get matches (matched & ambiguous)
    res_matches = client.get(f"/api/runs/{run_id}/matches?limit=10")
    assert res_matches.status_code == 200
    matches = res_matches.json()
    assert isinstance(matches, list)
    for m in matches:
        assert m["match_status"] in ["matched", "ambiguous"]

    # 3. Get unmatched with sensor filter
    res_unm_m = client.get(f"/api/runs/{run_id}/unmatched?sensor=MODIS")
    assert res_unm_m.status_code == 200
    unm_m = res_unm_m.json()
    for r in unm_m:
        assert r["match_status"] == "unmatched_modis"

    res_unm_v = client.get(f"/api/runs/{run_id}/unmatched?sensor=VIIRS")
    assert res_unm_v.status_code == 200
    unm_v = res_unm_v.json()
    for r in unm_v:
        assert r["match_status"] == "unmatched_viirs"


def test_evaluation_four_baselines_and_distributions(client, run_id):
    res_eval = client.get(f"/api/runs/{run_id}/summary")
    assert res_eval.status_code == 200
    data = res_eval.json()

    # Verify 4 mandatory baselines
    assert "four_baselines" in data
    four_baselines = data["four_baselines"]
    assert "modis_only" in four_baselines
    assert "viirs_only" in four_baselines
    assert "naive_concatenation" in four_baselines
    assert "proposed_harmonisation" in four_baselines

    modis_base = four_baselines["modis_only"]
    assert modis_base["valid_modis_count"] > 0
    assert "frp_mean" in modis_base
    assert "frp_median" in modis_base

    viirs_base = four_baselines["viirs_only"]
    assert viirs_base["valid_viirs_count"] > 0

    naive_base = four_baselines["naive_concatenation"]
    assert naive_base["total_naive_count"] == modis_base["valid_modis_count"] + viirs_base["valid_viirs_count"]

    harm_base = four_baselines["proposed_harmonisation"]
    assert harm_base["modis_match_rate_denominator"] == "valid_and_warning_modis_observations"

    # Verify FRP percentiles
    assert "frp_percentiles" in data
    assert "MODIS" in data["frp_percentiles"]
    assert "VIIRS" in data["frp_percentiles"]
    for p in ["p10", "p25", "p50", "p75", "p90"]:
        assert p in data["frp_percentiles"]["MODIS"]

    # Verify sensitivity grid
    assert len(data["sensitivity_grid"]) > 0


def test_custom_sensitivity_endpoint(client, run_id):
    custom_req = {
        "distance_grid_m": [500.0, 1000.0],
        "time_grid_s": [1800.0, 3600.0],
    }
    res = client.post(f"/api/runs/{run_id}/sensitivity", json=custom_req)
    assert res.status_code == 200
    points = res.json()
    assert len(points) == 4  # 2 distances x 2 times
    assert points[0]["spatial_threshold_m"] in [500.0, 1000.0]


def test_csv_export_and_reimportability(client, run_id):
    res = client.get(f"/api/runs/{run_id}/export?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "Content-Disposition" in res.headers
    assert f"harmonisation_{run_id}" in res.headers["Content-Disposition"]

    csv_text = res.text
    # Verify re-importability via pandas
    df = pd.read_csv(io.StringIO(csv_text))
    assert len(df) > 0
    assert "harmonisation_id" in df.columns
    assert "modis_frp_raw" in df.columns
    assert "viirs_frp_raw" in df.columns
    assert "spatial_distance_m" in df.columns


def test_geojson_export_validation(client, run_id):
    res = client.get(f"/api/runs/{run_id}/export?format=geojson")
    assert res.status_code == 200
    assert "application/geo+json" in res.headers["content-type"]
    assert "Content-Disposition" in res.headers

    geojson = res.json()
    assert geojson["type"] == "FeatureCollection"
    assert "metadata" in geojson
    assert geojson["metadata"]["run_id"] == run_id
    assert "scientific_limitations_note" in geojson["metadata"]
    assert len(geojson["features"]) > 0

    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert len(feature["geometry"]["coordinates"]) == 2
    assert "harmonisation_id" in feature["properties"]
    assert "match_status" in feature["properties"]
