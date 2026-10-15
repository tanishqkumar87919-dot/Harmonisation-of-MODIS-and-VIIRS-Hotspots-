"""Comprehensive Acceptance, Reproducibility, and Negative Test Suite.

Verifies all 9 Acceptance Tests from docs/10_TESTING_VALIDATION_DEPLOYMENT.md Section 4:
1. Known valid fixture loads and validates with exact expected counts.
2. Invalid fixture produces a detailed validation report with exact rejection reasons.
3. Reproducibility test (FR-14): Identical inputs produce byte-for-byte identical results.
4. Every output record contains non-null source provenance and links to source observations.
5. Unmatched MODIS and VIIRS observations are never discarded (observation conservation).
6. Ambiguous cases are represented according to each of the 3 ambiguity policies.
7. Negative API tests: 0-byte file, unsupported extensions, missing required columns,
   invalid thresholds, unknown run IDs all return proper status codes and structured errors.
8. Filtered queries and exported CSV/GeoJSON row counts match summary counts 100%.
9. Zero FRP averaging is strictly enforced across all outputs and metrics.
"""

import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.runs import (
    AmbiguityPolicy,
    MatchingParameters,
    MatchingQualityFilters,
    TimeWindowRule,
)
from backend.app.services.ingestion import IngestionService
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.standardization import StandardizationService

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"
MODIS_FIXTURE_PATH = FIXTURES_DIR / "sample_modis_fixture.csv"
VIIRS_FIXTURE_PATH = FIXTURES_DIR / "sample_viirs_fixture.csv"
INVALID_FIXTURE_PATH = FIXTURES_DIR / "invalid_modis_fixture.csv"
MANIFEST_PATH = FIXTURES_DIR / "FIXTURE_MANIFEST.json"


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Known valid fixtures load and validate with exact expected counts
# ---------------------------------------------------------------------------
def test_acceptance_1_known_valid_fixtures_load_with_exact_counts():
    assert MANIFEST_PATH.exists(), "FIXTURE_MANIFEST.json must exist"
    manifest = json.loads(MANIFEST_PATH.read_text())

    # 1. MODIS fixture validation
    modis_bytes = MODIS_FIXTURE_PATH.read_bytes()
    m_report, m_ds, m_df = IngestionService.inspect_and_validate(
        modis_bytes, source_uri="sample_modis_fixture.csv"
    )
    assert m_report.total_input_rows == 12
    assert m_report.valid_count == 10
    assert m_report.warning_count == 2
    assert m_report.rejected_count == 0
    assert m_ds.checksum == manifest["fixtures"]["sample_modis_fixture.csv"]["sha256"]

    # 2. VIIRS fixture validation
    viirs_bytes = VIIRS_FIXTURE_PATH.read_bytes()
    v_report, v_ds, v_df = IngestionService.inspect_and_validate(
        viirs_bytes, source_uri="sample_viirs_fixture.csv"
    )
    assert v_report.total_input_rows == 15
    assert v_report.valid_count == 13
    assert v_report.warning_count == 2
    assert v_report.rejected_count == 0
    assert v_ds.checksum == manifest["fixtures"]["sample_viirs_fixture.csv"]["sha256"]

    # 3. Check 17 internal standardized fields presence
    _, _, m_obs = StandardizationService.process_and_standardize(
        m_df, m_ds.id, m_report.sensor, m_ds.product_name, m_ds.product_version, "modis.csv", m_ds.checksum, "ir-1"
    )
    for obs in m_obs:
        assert obs.observation_id.startswith("obs-")
        assert obs.source_sensor.value == "MODIS"
        assert obs.platform in ["Terra", "Aqua"]
        assert -90.0 <= obs.latitude <= 90.0
        assert -180.0 <= obs.longitude <= 180.0
        assert obs.source_record_id.startswith("TEST_FIXTURE_MODIS_")


# ---------------------------------------------------------------------------
# Test 2: Invalid fixture produces a detailed validation report
# ---------------------------------------------------------------------------
def test_acceptance_2_invalid_fixture_detailed_validation_report():
    manifest = json.loads(MANIFEST_PATH.read_text())
    expected_rejections = manifest["fixtures"]["invalid_modis_fixture.csv"]["rejection_reasons"]

    invalid_bytes = INVALID_FIXTURE_PATH.read_bytes()
    report, ds, df = IngestionService.inspect_and_validate(
        invalid_bytes, source_uri="invalid_modis_fixture.csv"
    )

    assert report.total_input_rows == 6
    assert report.valid_count == 1
    assert report.warning_count == 0
    assert report.rejected_count == 5

    # Verify exact individual failure categories
    assert report.rejection_reasons["duplicate_source_row"] == expected_rejections["duplicate_source_row"]
    assert (
        report.rejection_reasons["invalid_or_out_of_range_latitude"]
        == expected_rejections["invalid_or_out_of_range_latitude"]
    )
    assert (
        report.rejection_reasons["invalid_or_out_of_range_longitude"]
        == expected_rejections["invalid_or_out_of_range_longitude"]
    )
    assert (
        report.rejection_reasons["malformed_or_missing_timestamp"]
        == expected_rejections["malformed_or_missing_timestamp"]
    )


# ---------------------------------------------------------------------------
# Test 3: Reproducibility test (FR-14)
# ---------------------------------------------------------------------------
def test_acceptance_3_reproducibility_identical_runs_produce_byte_for_byte_identical_results():
    with open(MODIS_FIXTURE_PATH, "rb") as f:
        _, m_ds, m_df = IngestionService.inspect_and_validate(f.read(), source_uri="modis.csv")
    with open(VIIRS_FIXTURE_PATH, "rb") as f:
        _, v_ds, v_df = IngestionService.inspect_and_validate(f.read(), source_uri="viirs.csv")

    _, _, m_obs1 = StandardizationService.process_and_standardize(
        m_df, "ds-m", m_ds.sensor, m_ds.product_name, m_ds.product_version, "m", "chk1", "ir1"
    )
    _, _, v_obs1 = StandardizationService.process_and_standardize(
        v_df, "ds-v", v_ds.sensor, v_ds.product_name, v_ds.product_version, "v", "chk2", "ir2"
    )

    params = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.RETAIN_AMBIGUOUS,
        quality_filters=MatchingQualityFilters(include_warnings=True),
    )

    # Run 1
    res1_records, _, res1_summary = MatchingEngine.execute_matching_run(
        run_id="run-repro-1",
        modis_observations=m_obs1,
        viirs_observations=v_obs1,
        parameters=params,
    )

    # Run 2
    res2_records, _, res2_summary = MatchingEngine.execute_matching_run(
        run_id="run-repro-2",
        modis_observations=m_obs1,
        viirs_observations=v_obs1,
        parameters=params,
    )

    # Summary counts and rates must be exactly identical
    assert res1_summary.counts.model_dump() == res2_summary.counts.model_dump()
    assert res1_summary.rates.model_dump() == res2_summary.rates.model_dump()

    assert len(res1_records) == len(res2_records)

    # Verify each harmonised record metrics match identically
    for r1, r2 in zip(res1_records, res2_records):
        assert r1.match_status == r2.match_status
        assert r1.spatial_distance_m == r2.spatial_distance_m
        assert r1.time_difference_s == r2.time_difference_s
        assert r1.match_score == r2.match_score
        assert r1.provenance.modis_source_record_id == r2.provenance.modis_source_record_id
        assert r1.provenance.viirs_source_record_id == r2.provenance.viirs_source_record_id


# ---------------------------------------------------------------------------
# Test 4: Every output record contains non-null source provenance
# ---------------------------------------------------------------------------
def test_acceptance_4_every_output_record_has_source_provenance():
    with open(MODIS_FIXTURE_PATH, "rb") as f:
        _, m_ds, m_df = IngestionService.inspect_and_validate(f.read(), source_uri="modis.csv")
    with open(VIIRS_FIXTURE_PATH, "rb") as f:
        _, v_ds, v_df = IngestionService.inspect_and_validate(f.read(), source_uri="viirs.csv")

    _, _, m_obs = StandardizationService.process_and_standardize(
        m_df, "ds-m", m_ds.sensor, m_ds.product_name, m_ds.product_version, "m", "chk1", "ir1"
    )
    _, _, v_obs = StandardizationService.process_and_standardize(
        v_df, "ds-v", v_ds.sensor, v_ds.product_name, v_ds.product_version, "v", "chk2", "ir2"
    )

    records, _, _ = MatchingEngine.execute_matching_run(
        run_id="run-prov-test",
        modis_observations=m_obs,
        viirs_observations=v_obs,
        parameters=MatchingParameters(),
    )

    for rec in records:
        assert rec.harmonisation_id is not None
        assert rec.matching_parameters is not None
        assert rec.matching_method_version is not None
        assert rec.provenance is not None

        if rec.match_status.value == "matched":
            assert rec.modis_observation_id is not None
            assert rec.viirs_observation_id is not None
            assert rec.provenance.modis_source_record_id is not None
            assert rec.provenance.viirs_source_record_id is not None
            assert rec.spatial_distance_m is not None
            assert rec.time_difference_s is not None
        elif rec.match_status.value == "unmatched_modis":
            assert rec.modis_observation_id is not None
            assert rec.viirs_observation_id is None
            assert rec.provenance.modis_source_record_id is not None
        elif rec.match_status.value == "unmatched_viirs":
            assert rec.viirs_observation_id is not None
            assert rec.modis_observation_id is None
            assert rec.provenance.viirs_source_record_id is not None


# ---------------------------------------------------------------------------
# Test 5: Unmatched MODIS and VIIRS observations are never discarded
# ---------------------------------------------------------------------------
def test_acceptance_5_unmatched_observations_never_discarded():
    with open(MODIS_FIXTURE_PATH, "rb") as f:
        _, m_ds, m_df = IngestionService.inspect_and_validate(f.read(), source_uri="modis.csv")
    with open(VIIRS_FIXTURE_PATH, "rb") as f:
        _, v_ds, v_df = IngestionService.inspect_and_validate(f.read(), source_uri="viirs.csv")

    _, _, m_obs = StandardizationService.process_and_standardize(
        m_df, "ds-m", m_ds.sensor, m_ds.product_name, m_ds.product_version, "m", "chk1", "ir1"
    )
    _, _, v_obs = StandardizationService.process_and_standardize(
        v_df, "ds-v", v_ds.sensor, v_ds.product_name, v_ds.product_version, "v", "chk2", "ir2"
    )

    q_filter = MatchingQualityFilters(include_warnings=True)
    eligible_m = StandardizationService.get_eligible_observations(
        m_obs, include_warnings=True
    )
    eligible_v = StandardizationService.get_eligible_observations(
        v_obs, include_warnings=True
    )

    for policy in [
        AmbiguityPolicy.RETAIN_AMBIGUOUS,
        AmbiguityPolicy.ONE_TO_ONE_DETERMINISTIC,
        AmbiguityPolicy.MANY_TO_MANY,
    ]:
        params = MatchingParameters(
            max_distance_meters=1500.0,
            max_time_difference_seconds=3600.0,
            ambiguity_policy=policy,
            quality_filters=q_filter,
        )
        records, _, _ = MatchingEngine.execute_matching_run(
            run_id=f"run-conserve-{policy.value}",
            modis_observations=eligible_m,
            viirs_observations=eligible_v,
            parameters=params,
        )

        modis_seen = set()
        viirs_seen = set()
        for r in records:
            if r.modis_observation_id:
                modis_seen.add(r.modis_observation_id)
            if r.viirs_observation_id:
                viirs_seen.add(r.viirs_observation_id)
            if r.candidate_links:
                for cl in r.candidate_links:
                    if cl.modis_observation_id:
                        modis_seen.add(cl.modis_observation_id)
                    if cl.viirs_observation_id:
                        viirs_seen.add(cl.viirs_observation_id)

        # Every eligible MODIS and VIIRS observation must be preserved and traceable
        assert modis_seen == {o.observation_id for o in eligible_m}
        assert viirs_seen == {o.observation_id for o in eligible_v}


# ---------------------------------------------------------------------------
# Test 6: Ambiguous cases are represented according to each of the 3 policies
# ---------------------------------------------------------------------------
def test_acceptance_6_ambiguous_policies_resolution():
    with open(MODIS_FIXTURE_PATH, "rb") as f:
        _, m_ds, m_df = IngestionService.inspect_and_validate(f.read(), source_uri="modis.csv")
    with open(VIIRS_FIXTURE_PATH, "rb") as f:
        _, v_ds, v_df = IngestionService.inspect_and_validate(f.read(), source_uri="viirs.csv")

    _, _, m_obs = StandardizationService.process_and_standardize(
        m_df, "ds-m", m_ds.sensor, m_ds.product_name, m_ds.product_version, "m", "chk1", "ir1"
    )
    _, _, v_obs = StandardizationService.process_and_standardize(
        v_df, "ds-v", v_ds.sensor, v_ds.product_name, v_ds.product_version, "v", "chk2", "ir2"
    )

    # 1. RETAIN_AMBIGUOUS
    p_retain = MatchingParameters(
        ambiguity_policy=AmbiguityPolicy.RETAIN_AMBIGUOUS,
        quality_filters=MatchingQualityFilters(include_warnings=True),
    )
    r_retain, _, s_retain = MatchingEngine.execute_matching_run(
        run_id="run-retain", modis_observations=m_obs, viirs_observations=v_obs, parameters=p_retain
    )
    assert s_retain.counts.matched_count == 5
    assert s_retain.counts.ambiguous_count == 1
    ambig_recs = [r for r in r_retain if r.match_status.value == "ambiguous"]
    assert len(ambig_recs) == 1  # 1 ambiguous cluster record
    assert len(ambig_recs[0].candidate_links) == 3  # Linked to 005A, 005B, 005C

    # 2. ONE_TO_ONE_DETERMINISTIC
    p_1to1 = MatchingParameters(
        ambiguity_policy=AmbiguityPolicy.ONE_TO_ONE_DETERMINISTIC,
        quality_filters=MatchingQualityFilters(include_warnings=True),
    )
    r_1to1, _, s_1to1 = MatchingEngine.execute_matching_run(
        run_id="run-1to1", modis_observations=m_obs, viirs_observations=v_obs, parameters=p_1to1
    )
    assert s_1to1.counts.matched_count == 6
    assert s_1to1.counts.ambiguous_count == 0
    # MODIS 005 must be deterministically matched to closest candidate VIIRS 005A
    match_005 = next(
        r for r in r_1to1 if r.provenance.modis_source_record_id == "TEST_FIXTURE_MODIS_005"
    )
    assert match_005.match_status.value == "matched"
    assert match_005.provenance.viirs_source_record_id == "TEST_FIXTURE_VIIRS_005A"

    # 3. MANY_TO_MANY
    p_m2m = MatchingParameters(
        ambiguity_policy=AmbiguityPolicy.MANY_TO_MANY,
        quality_filters=MatchingQualityFilters(include_warnings=True),
    )
    r_m2m, _, s_m2m = MatchingEngine.execute_matching_run(
        run_id="run-m2m", modis_observations=m_obs, viirs_observations=v_obs, parameters=p_m2m
    )
    assert s_m2m.counts.matched_count == 8
    assert s_m2m.counts.ambiguous_count == 0


# ---------------------------------------------------------------------------
# Test 7: Negative API tests
# ---------------------------------------------------------------------------
def test_acceptance_7_negative_api_tests(client):
    # 1. 0-byte upload
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert res.status_code == 422
    err_text = str(res.json().get("detail") or res.json().get("error", "")).lower()
    assert "empty" in err_text

    # 2. Unsupported extension (.exe)
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("malware.exe", b"fake binary content", "application/octet-stream")},
    )
    assert res.status_code == 422
    err_text = str(res.json().get("detail") or res.json().get("error", "")).lower()
    assert "extension" in err_text

    # 3. Unsupported extension (.json)
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("data.json", b'{"data": []}', "application/json")},
    )
    assert res.status_code == 422

    # 4. Missing required coordinate columns
    res = client.post(
        "/api/datasets/validate",
        files={"file": ("no_coords.csv", b"id,val1,val2\n1,a,b\n", "text/csv")},
    )
    assert res.status_code == 422
    err_text = str(res.json().get("detail") or res.json().get("error", "")).lower()
    assert "latitude" in err_text

    # 5. Non-existent run ID queries
    res = client.get("/api/runs/non-existent-uuid")
    assert res.status_code == 404
    assert res.json()["status_code"] == 404

    res = client.get("/api/runs/non-existent-uuid/matches")
    assert res.status_code == 404

    res = client.get("/api/runs/non-existent-uuid/summary")
    assert res.status_code == 404

    res = client.get("/api/runs/non-existent-uuid/export?format=csv")
    assert res.status_code == 404

    # 6. Invalid thresholds (negative spatial distance)
    res = client.post(
        "/api/runs",
        json={
            "modis_dataset_id": "dummy-m",
            "viirs_dataset_id": "dummy-v",
            "parameters": {
                "max_distance_meters": -500.0,
                "max_time_difference_seconds": 3600.0,
            },
        },
    )
    assert res.status_code == 422

    # 7. Invalid thresholds (negative temporal window)
    res = client.post(
        "/api/runs",
        json={
            "modis_dataset_id": "dummy-m",
            "viirs_dataset_id": "dummy-v",
            "parameters": {
                "max_distance_meters": 1500.0,
                "max_time_difference_seconds": -1800.0,
            },
        },
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Test 8: Filtered queries and exports match summary counts 100%
# ---------------------------------------------------------------------------
def test_acceptance_8_filtered_queries_and_exports_match_summary_counts(client):
    # Ingest fixtures via API
    m_res = client.post(
        "/api/datasets/validate",
        files={"file": ("modis_test.csv", MODIS_FIXTURE_PATH.read_bytes(), "text/csv")},
    )
    assert m_res.status_code in (200, 201)
    m_id = m_res.json()["dataset_id"]

    v_res = client.post(
        "/api/datasets/validate",
        files={"file": ("viirs_test.csv", VIIRS_FIXTURE_PATH.read_bytes(), "text/csv")},
    )
    assert v_res.status_code in (200, 201)
    v_id = v_res.json()["dataset_id"]

    # Launch processing run
    run_res = client.post(
        "/api/runs",
        json={
            "modis_dataset_id": m_id,
            "viirs_dataset_id": v_id,
            "parameters": {
                "max_distance_meters": 1500.0,
                "max_time_difference_seconds": 3600.0,
                "ambiguity_policy": "retain_ambiguous",
            },
        },
    )
    assert run_res.status_code == 201
    summary = run_res.json()
    run_id = summary["run_id"]

    matched_count = summary["counts"]["matched_count"]
    ambiguous_count = summary["counts"]["ambiguous_count"]
    unmatched_m_count = summary["counts"]["unmatched_modis_count"]
    unmatched_v_count = summary["counts"]["unmatched_viirs_count"]

    # 1. Matches endpoint count (filtered by matched status and unfiltered)
    matches_res = client.get(f"/api/runs/{run_id}/matches?match_status=matched&limit=1000")
    assert matches_res.status_code == 200
    matches_data = matches_res.json()
    assert len(matches_data) == matched_count

    all_matches_res = client.get(f"/api/runs/{run_id}/matches?limit=1000")
    assert all_matches_res.status_code == 200
    assert len(all_matches_res.json()) == matched_count + ambiguous_count

    # 2. Unmatched endpoint counts
    unmatched_res = client.get(f"/api/runs/{run_id}/unmatched?limit=1000")
    assert unmatched_res.status_code == 200
    unmatched_data = unmatched_res.json()
    assert len(unmatched_data) == unmatched_m_count + unmatched_v_count

    unmatched_modis_res = client.get(f"/api/runs/{run_id}/unmatched?sensor=MODIS&limit=1000")
    assert unmatched_modis_res.status_code == 200
    assert len(unmatched_modis_res.json()) == unmatched_m_count

    unmatched_viirs_res = client.get(f"/api/runs/{run_id}/unmatched?sensor=VIIRS&limit=1000")
    assert unmatched_viirs_res.status_code == 200
    assert len(unmatched_viirs_res.json()) == unmatched_v_count

    # 3. CSV export data row count matches total harmonised records
    csv_res = client.get(f"/api/runs/{run_id}/export?format=csv")
    assert csv_res.status_code == 200
    lines = [
        line.strip()
        for line in csv_res.text.strip().split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    # lines[0] is header, remaining are data rows
    csv_data_row_count = len(lines) - 1
    total_harmonised_records = matched_count + ambiguous_count + unmatched_m_count + unmatched_v_count
    assert csv_data_row_count == total_harmonised_records

    # 4. GeoJSON export features count matches total harmonised records
    geojson_res = client.get(f"/api/runs/{run_id}/export?format=geojson")
    assert geojson_res.status_code == 200
    features = geojson_res.json()["features"]
    assert len(features) == total_harmonised_records


# ---------------------------------------------------------------------------
# Test 9: Zero FRP averaging is strictly enforced
# ---------------------------------------------------------------------------
def test_acceptance_9_zero_frp_averaging_enforced(client):
    with open(MODIS_FIXTURE_PATH, "rb") as f:
        _, m_ds, m_df = IngestionService.inspect_and_validate(f.read(), source_uri="modis.csv")
    with open(VIIRS_FIXTURE_PATH, "rb") as f:
        _, v_ds, v_df = IngestionService.inspect_and_validate(f.read(), source_uri="viirs.csv")

    _, _, m_obs = StandardizationService.process_and_standardize(
        m_df, "ds-m", m_ds.sensor, m_ds.product_name, m_ds.product_version, "m", "chk1", "ir1"
    )
    _, _, v_obs = StandardizationService.process_and_standardize(
        v_df, "ds-v", v_ds.sensor, v_ds.product_name, v_ds.product_version, "v", "chk2", "ir2"
    )

    records, _, summary = MatchingEngine.execute_matching_run(
        run_id="run-frp-check",
        modis_observations=m_obs,
        viirs_observations=v_obs,
        parameters=MatchingParameters(),
    )

    matched_pairs = [r for r in records if r.match_status.value == "matched"]
    assert len(matched_pairs) > 0

    for pair in matched_pairs:
        assert pair.modis_observation is not None
        assert pair.viirs_observation is not None
        m_frp = pair.modis_observation.frp_raw
        v_frp = pair.viirs_observation.frp_raw

        assert m_frp is not None
        assert v_frp is not None
        assert m_frp != v_frp, "MODIS (1km) and VIIRS (375m) FRP should not be synthetically equalized"

        # Ensure no synthetic 'average_frp' or 'frp' attribute exists
        record_dict = pair.model_dump()
        assert "average_frp" not in record_dict
        assert "harmonised_frp" not in record_dict
        assert "mean_frp" not in record_dict

    # Check scientific disclaimer in evaluation summary
    from backend.app.services.evaluation import EvaluationService

    evaluation = EvaluationService.generate_evaluation(
        summary=summary,
        records=records,
        modis_observations=m_obs,
        viirs_observations=v_obs,
    )
    assert evaluation.frp_distribution is not None
    assert "not be averaged" in evaluation.frp_distribution.scientific_disclaimer.lower()
