#!/usr/bin/env python3
"""
Seed Labelled Verification Fixtures Script.
Ingests curated MODIS and VIIRS verification fixtures (data/samples/sample_modis_fixture.csv
and data/samples/sample_viirs_fixture.csv), initializes database tables, executes a reference
harmonisation run, and reports summary counts.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure repository root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from backend.app.config import settings
from backend.app.db.models import (
    Base,
    DatasetModel,
    HarmonisedRecordModel,
    MatchCandidateModel,
    ObservationModel,
    ProcessingRunModel,
)
from backend.app.db.session import engine, SessionLocal, init_db_extensions
from backend.app.schemas.common import AmbiguityPolicy, MatchStatus, SensorType
from backend.app.schemas.matching import MatchingParameters, MatchingQualityFilters
from backend.app.services.evaluation import EvaluationService
from backend.app.services.ingestion import IngestionService
from backend.app.services.matching_engine import MatchingEngineService
from backend.app.services.repository import repo
from backend.app.services.standardization import StandardizationService


def seed_fixtures():
    # 1. Initialize DB tables
    init_db_extensions(engine)
    Base.metadata.create_all(bind=engine)

    samples_dir = REPO_ROOT / "data" / "samples"
    modis_file = samples_dir / "sample_modis_fixture.csv"
    viirs_file = samples_dir / "sample_viirs_fixture.csv"

    if not modis_file.exists():
        raise FileNotFoundError(f"MODIS fixture file not found: {modis_file}")
    if not viirs_file.exists():
        raise FileNotFoundError(f"VIIRS fixture file not found: {viirs_file}")

    print(f"Reading MODIS fixture: {modis_file}")
    with open(modis_file, "rb") as f:
        modis_bytes = f.read()

    print(f"Reading VIIRS fixture: {viirs_file}")
    with open(viirs_file, "rb") as f:
        viirs_bytes = f.read()

    # 2. Ingest and Standardize MODIS fixture
    df_m_raw, _, checksum_m = IngestionService.parse_raw_csv(modis_bytes, "sample_modis_fixture.csv")
    renamed_m, _ = IngestionService.normalize_column_names(df_m_raw)
    modis_ds_id = f"fixture-modis-{uuid.uuid4().hex[:8]}"

    _, ds_m, obs_m = StandardizationService.process_and_standardize(
        df_raw=renamed_m,
        dataset_id=modis_ds_id,
        sensor=SensorType.MODIS,
        product_name="MOD14_Terra_Collection_6_1",
        product_version="C6.1",
        source_uri="data/samples/sample_modis_fixture.csv",
        checksum=checksum_m,
        ingestion_run_id=f"ingest-{uuid.uuid4().hex[:8]}",
        is_test_fixture=True,
    )
    repo.save_dataset(ds_m, obs_m, raw_bytes=modis_bytes)

    # 3. Ingest and Standardize VIIRS fixture
    df_v_raw, _, checksum_v = IngestionService.parse_raw_csv(viirs_bytes, "sample_viirs_fixture.csv")
    renamed_v, _ = IngestionService.normalize_column_names(df_v_raw)
    viirs_ds_id = f"fixture-viirs-{uuid.uuid4().hex[:8]}"

    _, ds_v, obs_v = StandardizationService.process_and_standardize(
        df_raw=renamed_v,
        dataset_id=viirs_ds_id,
        sensor=SensorType.VIIRS,
        product_name="VNP14IMGTDL_NPP_Collection_1",
        product_version="v1.0",
        source_uri="data/samples/sample_viirs_fixture.csv",
        checksum=checksum_v,
        ingestion_run_id=f"ingest-{uuid.uuid4().hex[:8]}",
        is_test_fixture=True,
    )
    repo.save_dataset(ds_v, obs_v, raw_bytes=viirs_bytes)

    # 4. Insert into database session
    with SessionLocal() as session:
        # Check if dataset already in DB
        modis_uuid = uuid.uuid4()
        viirs_uuid = uuid.uuid4()

        m_db_ds = DatasetModel(
            id=modis_uuid,
            sensor="MODIS",
            product_name=ds_m.product_name,
            product_version=ds_m.product_version,
            source_uri=ds_m.source_uri,
            retrieved_at=datetime.now(timezone.utc),
            checksum=checksum_m,
            metadata_json={"is_test_fixture": True, "dataset_id": modis_ds_id},
        )
        v_db_ds = DatasetModel(
            id=viirs_uuid,
            sensor="VIIRS",
            product_name=ds_v.product_name,
            product_version=ds_v.product_version,
            source_uri=ds_v.source_uri,
            retrieved_at=datetime.now(timezone.utc),
            checksum=checksum_v,
            metadata_json={"is_test_fixture": True, "dataset_id": viirs_ds_id},
        )
        session.add_all([m_db_ds, v_db_ds])
        session.flush()

        obs_id_to_uuid = {}
        for o in obs_m:
            o_uuid = uuid.uuid4()
            obs_id_to_uuid[o.observation_id] = o_uuid
            session.add(
                ObservationModel(
                    id=o_uuid,
                    dataset_id=modis_uuid,
                    source_record_id=o.source_record_id,
                    sensor="MODIS",
                    observed_at=datetime.fromisoformat(o.observation_time_utc) if o.observation_time_utc else None,
                    latitude=o.latitude,
                    longitude=o.longitude,
                    confidence_raw=str(o.confidence_raw) if o.confidence_raw is not None else None,
                    frp_raw=o.frp_raw,
                    frp_unit=o.frp_unit,
                    raw_fields=o.raw_fields,
                    quality_status=o.row_quality_status.value if hasattr(o.row_quality_status, "value") else str(o.row_quality_status),
                    quality_notes=o.quality_notes,
                )
            )

        for o in obs_v:
            o_uuid = uuid.uuid4()
            obs_id_to_uuid[o.observation_id] = o_uuid
            session.add(
                ObservationModel(
                    id=o_uuid,
                    dataset_id=viirs_uuid,
                    source_record_id=o.source_record_id,
                    sensor="VIIRS",
                    observed_at=datetime.fromisoformat(o.observation_time_utc) if o.observation_time_utc else None,
                    latitude=o.latitude,
                    longitude=o.longitude,
                    confidence_raw=str(o.confidence_raw) if o.confidence_raw is not None else None,
                    frp_raw=o.frp_raw,
                    frp_unit=o.frp_unit,
                    raw_fields=o.raw_fields,
                    quality_status=o.row_quality_status.value if hasattr(o.row_quality_status, "value") else str(o.row_quality_status),
                    quality_notes=o.quality_notes,
                )
            )

        session.commit()

    # 5. Execute reference harmonisation run
    params = MatchingParameters(
        max_distance_meters=1000.0,
        max_time_difference_seconds=1800.0,
        ambiguity_policy=AmbiguityPolicy.RETAIN_AMBIGUOUS,
        matching_method_version="v1.0.0-phase2-ref",
        quality_filters=MatchingQualityFilters(include_warnings=True),
    )

    eligible_modis = StandardizationService.get_eligible_observations(
        obs_m,
        include_warnings=True,
    )
    eligible_viirs = StandardizationService.get_eligible_observations(
        obs_v,
        include_warnings=True,
    )

    run_id = f"run-fixture-{uuid.uuid4().hex[:8]}"

    engine_result = MatchingEngineService.run_harmonisation(
        run_id=run_id,
        modis_observations=eligible_modis,
        viirs_observations=eligible_viirs,
        parameters=params,
        modis_input_count=ds_m.total_rows,
        viirs_input_count=ds_v.total_rows,
        modis_warning_count=ds_m.warning_rows,
        viirs_warning_count=ds_v.warning_rows,
        modis_rejected_count=ds_m.rejected_rows,
        viirs_rejected_count=ds_v.rejected_rows,
    )

    records = engine_result.harmonised_records
    candidates = engine_result.match_candidates
    summary = engine_result.summary_report

    evaluation = EvaluationService.generate_evaluation(
        summary=summary,
        records=records,
        modis_observations=eligible_modis,
        viirs_observations=eligible_viirs,
    )

    # Save into in-memory repo
    repo.save_run(summary, records, candidates, evaluation)

    # 6. Save run, candidates, and harmonised records into database
    with SessionLocal() as session:
        run_uuid = uuid.uuid4()
        params_dict = params.model_dump() if hasattr(params, "model_dump") else params.dict()
        params_dict["original_run_id"] = run_id
        db_run = ProcessingRunModel(
            id=run_uuid,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status="succeeded",
            method_version=params.matching_method_version,
            parameters=params_dict,
            input_dataset_ids={"modis": modis_ds_id, "viirs": viirs_ds_id},
            summary=summary.model_dump() if hasattr(summary, "model_dump") else summary.dict(),
        )
        session.add(db_run)
        session.flush()

        for c in candidates:
            m_uid = obs_id_to_uuid.get(c.modis_observation_id)
            v_uid = obs_id_to_uuid.get(c.viirs_observation_id)
            if m_uid and v_uid:
                cand_dec = c.decision.value if hasattr(c.decision, "value") else str(c.decision)
                session.add(
                    MatchCandidateModel(
                        run_id=run_uuid,
                        modis_observation_id=m_uid,
                        viirs_observation_id=v_uid,
                        spatial_distance_m=c.spatial_distance_m,
                        time_difference_s=c.time_difference_s,
                        score=c.score,
                        decision=cand_dec,
                        decision_reason=c.decision_reason,
                    )
                )

        for r in records:
            rec_status = r.match_status.value if hasattr(r.match_status, "value") else str(r.match_status)
            m_uid = obs_id_to_uuid.get(r.modis_observation_id) if r.modis_observation_id else None
            v_uid = obs_id_to_uuid.get(r.viirs_observation_id) if r.viirs_observation_id else None
            attrs = {
                "spatial_distance_m": r.spatial_distance_m,
                "time_difference_s": r.time_difference_s,
                "match_score": r.match_score,
                "review_status": r.review_status.value if hasattr(r.review_status, "value") else str(r.review_status),
            }
            prov = r.provenance.model_dump() if hasattr(r.provenance, "model_dump") else dict(r.provenance or {})
            session.add(
                HarmonisedRecordModel(
                    run_id=run_uuid,
                    match_status=rec_status,
                    modis_observation_id=m_uid,
                    viirs_observation_id=v_uid,
                    attributes=attrs,
                    provenance=prov,
                )
            )

        session.commit()

    # 7. Print requested outputs to terminal
    matched_count = summary.counts.matched_count
    unmatched_modis_count = summary.counts.unmatched_modis_count
    unmatched_viirs_count = summary.counts.unmatched_viirs_count
    ambiguous_count = summary.counts.ambiguous_count

    print("=" * 65)
    print("FIXTURE SEEDING & REFERENCE HARMONISATION COMPLETED")
    print("=" * 65)
    print(f"MODIS Dataset ID : {modis_ds_id} (Rows: {ds_m.total_rows}, Valid: {ds_m.valid_rows})")
    print(f"VIIRS Dataset ID : {viirs_ds_id} (Rows: {ds_v.total_rows}, Valid: {ds_v.valid_rows})")
    print(f"Run ID           : {run_id}")
    print("-" * 65)
    print("Match Counts:")
    print(f"  - Matched Detections       : {matched_count}")
    print(f"  - Unmatched MODIS          : {unmatched_modis_count}")
    print(f"  - Unmatched VIIRS          : {unmatched_viirs_count}")
    print(f"  - Ambiguous Clusters       : {ambiguous_count}")
    print("-" * 65)
    print("Baseline Comparison Table:")
    print(f"  {'Baseline Strategy':<30} | {'Total Records':<14} | {'Unique Locations':<18} | {'Est. Duplicates':<15}")
    print("  " + "-" * 85)
    for b in evaluation.baselines:
        print(f"  {b.name:<30} | {b.total_records:<14} | {b.unique_time_locations:<18} | {b.duplicate_estimate:<15}")
    print("=" * 90)

    return {
        "modis_dataset_id": modis_ds_id,
        "viirs_dataset_id": viirs_ds_id,
        "run_id": run_id,
        "matched": matched_count,
        "unmatched_modis": unmatched_modis_count,
        "unmatched_viirs": unmatched_viirs_count,
        "ambiguous": ambiguous_count,
    }


if __name__ == "__main__":
    seed_fixtures()
