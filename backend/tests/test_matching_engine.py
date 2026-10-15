"""Phase 3 Acceptance & Verification: Matching Engine and 9 Edge Cases."""

import pytest
from backend.app.schemas.datasets import RowQualityStatus, SensorType
from backend.app.schemas.observations import StandardizedObservationSchema
from backend.app.schemas.runs import (
    AmbiguityPolicy,
    CandidateDecision,
    MatchingParameters,
    MatchStatus,
)
from backend.app.services.matching_engine import MatchingEngineService


def make_obs(
    obs_id: str,
    sensor: SensorType,
    lat: float,
    lon: float,
    time_utc: str,
    frp: float = 20.0,
    conf: str = "80",
    status: RowQualityStatus = RowQualityStatus.VALID,
) -> StandardizedObservationSchema:
    return StandardizedObservationSchema(
        observation_id=obs_id,
        dataset_id=f"ds-{sensor.value.lower()}",
        source_record_id=f"rec-{obs_id}",
        source_sensor=sensor,
        platform="Terra" if sensor == SensorType.MODIS else "Suomi-NPP",
        product_name="MOD14" if sensor == SensorType.MODIS else "VNP14",
        product_version="1.0",
        observation_time_utc=time_utc,
        latitude=lat,
        longitude=lon,
        confidence_raw=conf,
        frp_raw=frp,
        frp_unit="MW",
        scan_raw=1.0,
        track_raw=1.0,
        quality_flags_raw={},
        ingestion_run_id="run-1",
        row_quality_status=status,
        quality_notes=[],
        raw_fields={},
    )


# 1. Identical coordinates and times (distance = 0m, time_diff = 0s)
def test_edge_case_1_identical_coordinates_and_times():
    m = [make_obs("m1", SensorType.MODIS, 28.5, 77.2, "2023-05-01T06:00:00Z")]
    v = [make_obs("v1", SensorType.VIIRS, 28.5, 77.2, "2023-05-01T06:00:00Z")]

    params = MatchingParameters(max_distance_meters=1500.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec1", m, v, params)

    assert len(res.harmonised_records) == 1
    rec = res.harmonised_records[0]
    assert rec.match_status == MatchStatus.MATCHED
    assert rec.spatial_distance_m == 0.0
    assert rec.time_difference_s == 0.0
    assert rec.match_score == 1.0


# 2. Same location (0m) but time difference above threshold (unmatched)
def test_edge_case_2_same_location_time_exceeded():
    m = [make_obs("m1", SensorType.MODIS, 28.5, 77.2, "2023-05-01T04:00:00Z")]
    v = [make_obs("v1", SensorType.VIIRS, 28.5, 77.2, "2023-05-01T06:00:00Z")]  # 7200s apart

    params = MatchingParameters(max_distance_meters=1500.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec2", m, v, params)

    assert len(res.match_candidates) == 0
    assert len(res.unmatched_modis_records) == 1
    assert len(res.unmatched_viirs_records) == 1


# 3. Close times (30s) but spatial distance above threshold (unmatched)
def test_edge_case_3_close_times_spatial_exceeded():
    m = [make_obs("m1", SensorType.MODIS, 28.50, 77.20, "2023-05-01T06:00:00Z")]
    v = [make_obs("v1", SensorType.VIIRS, 28.60, 77.20, "2023-05-01T06:00:30Z")]  # ~11.1km apart

    params = MatchingParameters(max_distance_meters=1500.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec3", m, v, params)

    assert len(res.match_candidates) == 0
    assert len(res.unmatched_modis_records) == 1
    assert len(res.unmatched_viirs_records) == 1


# 4. One MODIS record with multiple VIIRS candidates under all 3 ambiguity policies
def test_edge_case_4_ambiguity_policies():
    m = [make_obs("m1", SensorType.MODIS, 28.5000, 77.2000, "2023-05-01T06:00:00Z")]
    # v1 is closer, v2 is slightly farther
    v1 = make_obs("v1", SensorType.VIIRS, 28.5010, 77.2000, "2023-05-01T06:05:00Z")  # ~111m
    v2 = make_obs("v2", SensorType.VIIRS, 28.5040, 77.2000, "2023-05-01T06:10:00Z")  # ~444m
    v = [v1, v2]

    # Policy A: retain_ambiguous (Default)
    params_a = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.RETAIN_AMBIGUOUS,
    )
    res_a = MatchingEngineService.run_harmonisation("run-ec4a", m, v, params_a)
    assert len(res_a.ambiguous_records) == 1
    assert res_a.ambiguous_records[0].provenance.candidate_count == 2
    assert len(res_a.unmatched_viirs_records) == 0

    # Policy B: one_to_one_deterministic
    params_b = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.ONE_TO_ONE_DETERMINISTIC,
    )
    res_b = MatchingEngineService.run_harmonisation("run-ec4b", m, v, params_b)
    # v1 should be matched, v2 should be rejected/unmatched
    assert len(res_b.summary_report.counts.matched_count == 1 and [1] or []) == 1
    matched_rec = [r for r in res_b.harmonised_records if r.match_status == MatchStatus.MATCHED][0]
    assert matched_rec.viirs_observation_id == "v1"
    assert len(res_b.unmatched_viirs_records) == 1
    assert res_b.unmatched_viirs_records[0].viirs_observation_id == "v2"

    # Policy C: many_to_many
    params_c = MatchingParameters(
        max_distance_meters=1500.0,
        max_time_difference_seconds=3600.0,
        ambiguity_policy=AmbiguityPolicy.MANY_TO_MANY,
    )
    res_c = MatchingEngineService.run_harmonisation("run-ec4c", m, v, params_c)
    assert res_c.summary_report.counts.matched_count == 2


# 5. Missing timestamp or coordinates (rejected in QC, never crashes matching)
def test_edge_case_5_missing_coordinates_or_timestamp():
    m = [
        make_obs("m_good", SensorType.MODIS, 28.5, 77.2, "2023-05-01T06:00:00Z"),
        make_obs("m_bad", SensorType.MODIS, 0.0, 0.0, "", status=RowQualityStatus.REJECTED),
    ]
    v = [make_obs("v1", SensorType.VIIRS, 28.5, 77.2, "2023-05-01T06:00:00Z")]

    params = MatchingParameters(max_distance_meters=1500.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec5", m, v, params)

    assert res.summary_report.counts.matched_count == 1
    assert not any(r.modis_observation_id == "m_bad" for r in res.harmonised_records)


# 6. Duplicate source rows (rejected in QC)
def test_edge_case_6_duplicate_source_rows():
    m = [
        make_obs("m1", SensorType.MODIS, 28.5, 77.2, "2023-05-01T06:00:00Z"),
        make_obs("m1_dup", SensorType.MODIS, 28.5, 77.2, "2023-05-01T06:00:00Z", status=RowQualityStatus.REJECTED),
    ]
    v = [make_obs("v1", SensorType.VIIRS, 28.5, 77.2, "2023-05-01T06:00:00Z")]

    params = MatchingParameters(max_distance_meters=1500.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec6", m, v, params)

    assert res.summary_report.counts.matched_count == 1


# 7. Dateline-crossing coordinates (179.999 and -179.999 -> ~222m geodesic distance -> matched)
def test_edge_case_7_dateline_crossing():
    m = [make_obs("m_dateline", SensorType.MODIS, 0.0, 179.999, "2023-05-01T06:00:00Z")]
    v = [make_obs("v_dateline", SensorType.VIIRS, 0.0, -179.999, "2023-05-01T06:00:00Z")]

    params = MatchingParameters(max_distance_meters=1000.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec7", m, v, params)

    # 0.002 degrees at equator is ~222.6m
    assert len(res.match_candidates) == 1
    cand = res.match_candidates[0]
    assert 200.0 < cand.spatial_distance_m < 250.0
    assert res.summary_report.counts.matched_count == 1


# 8. Records at study-area boundaries
def test_edge_case_8_study_area_boundaries():
    m = [make_obs("m_north_pole", SensorType.MODIS, 85.0, 0.0, "2023-05-01T06:00:00Z")]
    v = [make_obs("v_north_pole", SensorType.VIIRS, 85.001, 0.0, "2023-05-01T06:00:00Z")]

    params = MatchingParameters(max_distance_meters=1500.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec8", m, v, params)

    assert len(res.match_candidates) == 1
    assert res.summary_report.counts.matched_count == 1


# 9. Empty input and single-sensor-only input
def test_edge_case_9_single_sensor_only_preservation():
    m = [
        make_obs("m1", SensorType.MODIS, 28.5, 77.2, "2023-05-01T06:00:00Z"),
        make_obs("m2", SensorType.MODIS, 28.6, 77.3, "2023-05-01T06:00:00Z"),
    ]
    v = []  # VIIRS empty

    params = MatchingParameters(max_distance_meters=1500.0, max_time_difference_seconds=3600.0)
    res = MatchingEngineService.run_harmonisation("run-ec9", m, v, params)

    assert len(res.match_candidates) == 0
    assert res.summary_report.counts.matched_count == 0
    assert len(res.unmatched_modis_records) == 2
    assert len(res.unmatched_viirs_records) == 0
