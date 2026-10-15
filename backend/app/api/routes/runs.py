"""Processing run endpoints for harmonisation execution, records inspection, sensitivity, and exports."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.db.models import (
    HarmonisedRecordModel,
    MatchCandidateModel,
    ProcessingRunModel,
)
from backend.app.db.repositories import (
    DatasetRepository,
    ObservationRepository,
    ProcessingRunRepository,
    ensure_uuid,
)
from backend.app.db.session import get_db
from backend.app.schemas.common import MatchStatus, SensorType
from backend.app.schemas.matching import HarmonisedRecord, RunCreateRequest
from backend.app.schemas.runs import (
    CustomSensitivityRequest,
    ProcessingRunSummary,
    RunDetailedEvaluation,
    SensitivityGridPoint,
)
from backend.app.services.evaluation import EvaluationService
from backend.app.services.exporter import ExporterService
from backend.app.services.matching_engine import MatchingEngineService
from backend.app.services.repository import repo
from backend.app.services.standardization import StandardizationService

router = APIRouter(prefix="/runs", tags=["Processing Runs"])


def sanitize_error_message(exc: Exception) -> str:
    """Mask credentials or connection secrets from database or system exception messages."""
    msg = str(exc)
    for sensitive in ("password", "secret", "token", "key", "credential", "postgres://", "postgresql://"):
        if sensitive in msg.lower():
            return "Internal processing failure occurred. Error details masked for security."
    return msg[:500]


def run_model_to_summary(model: ProcessingRunModel) -> ProcessingRunSummary:
    """Convert ProcessingRunModel to ProcessingRunSummary schema."""
    if model.summary and isinstance(model.summary, dict) and "run_id" in model.summary:
        return ProcessingRunSummary(**model.summary)

    params = model.parameters or {}
    inputs = model.input_dataset_ids or {}
    return ProcessingRunSummary(
        run_id=params.get("original_run_id") or str(model.id),
        started_at=model.started_at.isoformat() if model.started_at else datetime.now(timezone.utc).isoformat(),
        completed_at=model.completed_at.isoformat() if model.completed_at else None,
        status=model.status,
        method_version=model.method_version,
        parameters=params,
        input_dataset_ids=inputs,
        counts={"total_records": 0, "matched": 0, "unmatched_modis": 0, "unmatched_viirs": 0, "ambiguous": 0},
        baseline_comparison=[],
        quality_summary={},
        execution_duration_ms=0,
        error_summary=model.error_summary,
    )


@router.post("", response_model=ProcessingRunSummary, status_code=status.HTTP_201_CREATED)
def create_processing_run(
    payload: RunCreateRequest,
    db: Session = Depends(get_db),
) -> ProcessingRunSummary:
    """
    Launch a reproducible harmonisation run linking MODIS and VIIRS datasets.
    Implements managed transaction boundaries, failure rollback protection,
    and partial-output prevention (docs/06_SYSTEM_ARCHITECTURE.md Section 5).
    """
    db_ds_repo = DatasetRepository(db)
    db_obs_repo = ObservationRepository(db)
    db_run_repo = ProcessingRunRepository(db)

    # Resolve MODIS dataset
    modis_ds = db_ds_repo.get(payload.modis_dataset_id) or repo.get_dataset(payload.modis_dataset_id)
    if not modis_ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MODIS dataset '{payload.modis_dataset_id}' not found.",
        )

    # Resolve VIIRS dataset
    viirs_ds = db_ds_repo.get(payload.viirs_dataset_id) or repo.get_dataset(payload.viirs_dataset_id)
    if not viirs_ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VIIRS dataset '{payload.viirs_dataset_id}' not found.",
        )

    run_uuid = uuid.uuid4()
    run_str_id = f"run-{run_uuid.hex[:12]}"
    now = datetime.now(timezone.utc)

    params_dict = payload.parameters.model_dump()
    params_dict["original_run_id"] = run_str_id
    inputs_dict = {
        "modis_dataset_id": payload.modis_dataset_id,
        "viirs_dataset_id": payload.viirs_dataset_id,
    }

    # 1. Insert initial ProcessingRunModel row with status='running' and commit
    run_model = ProcessingRunModel(
        id=run_uuid,
        started_at=now,
        completed_at=None,
        status="running",
        method_version="1.0.0",
        parameters=params_dict,
        input_dataset_ids=inputs_dict,
        summary=None,
        error_summary=None,
    )
    db.add(run_model)
    db.commit()

    # 2. Managed execution inside rollback protection block
    try:
        # Load eligible observations
        q_filters = payload.parameters.quality_filters
        db_m_obs = db_obs_repo.get_eligible(
            payload.modis_dataset_id,
            include_warnings=q_filters.include_warnings,
            min_modis_confidence=q_filters.min_modis_confidence,
        )
        db_v_obs = db_obs_repo.get_eligible(
            payload.viirs_dataset_id,
            include_warnings=q_filters.include_warnings,
            allowed_viirs_confidence_levels=q_filters.allowed_viirs_confidence_levels,
        )

        if db_m_obs and db_v_obs:
            from backend.app.api.routes.datasets import obs_model_to_schema
            eligible_modis = [obs_model_to_schema(o) for o in db_m_obs]
            eligible_viirs = [obs_model_to_schema(o) for o in db_v_obs]
        else:
            all_modis_obs = repo.get_observations(payload.modis_dataset_id)
            all_viirs_obs = repo.get_observations(payload.viirs_dataset_id)
            eligible_modis = StandardizationService.get_eligible_observations(
                all_modis_obs,
                include_warnings=q_filters.include_warnings,
                min_modis_confidence=q_filters.min_modis_confidence,
            )
            eligible_viirs = StandardizationService.get_eligible_observations(
                all_viirs_obs,
                include_warnings=q_filters.include_warnings,
                allowed_viirs_confidence_levels=q_filters.allowed_viirs_confidence_levels,
            )

        m_meta = getattr(modis_ds, "metadata_json", {}) or {}
        v_meta = getattr(viirs_ds, "metadata_json", {}) or {}
        modis_total = getattr(modis_ds, "total_rows", m_meta.get("total_rows", len(eligible_modis)))
        viirs_total = getattr(viirs_ds, "total_rows", v_meta.get("total_rows", len(eligible_viirs)))
        modis_warn = getattr(modis_ds, "warning_rows", m_meta.get("warning_rows", 0))
        viirs_warn = getattr(viirs_ds, "warning_rows", v_meta.get("warning_rows", 0))
        modis_rej = getattr(modis_ds, "rejected_rows", m_meta.get("rejected_rows", 0))
        viirs_rej = getattr(viirs_ds, "rejected_rows", v_meta.get("rejected_rows", 0))

        engine_result = MatchingEngineService.run_harmonisation(
            run_id=run_str_id,
            modis_observations=eligible_modis,
            viirs_observations=eligible_viirs,
            parameters=payload.parameters,
            modis_input_count=modis_total,
            viirs_input_count=viirs_total,
            modis_warning_count=modis_warn,
            viirs_warning_count=viirs_warn,
            modis_rejected_count=modis_rej,
            viirs_rejected_count=viirs_rej,
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

        # Build ORM model lists for bulk persistence
        candidate_models: List[MatchCandidateModel] = []
        for cand in candidates:
            cand_dec = cand.decision.value if hasattr(cand.decision, "value") else str(cand.decision)
            candidate_models.append(
                MatchCandidateModel(
                    run_id=run_uuid,
                    modis_observation_id=ensure_uuid(cand.modis_observation_id),
                    viirs_observation_id=ensure_uuid(cand.viirs_observation_id),
                    spatial_distance_m=cand.spatial_distance_m,
                    time_difference_s=cand.time_difference_s,
                    score=cand.score,
                    decision=cand_dec,
                    decision_reason=cand.decision_reason,
                )
            )

        record_models: List[HarmonisedRecordModel] = []
        for rec in records:
            rec_status = rec.match_status.value if hasattr(rec.match_status, "value") else str(rec.match_status)
            attrs = {
                "spatial_distance_m": rec.spatial_distance_m,
                "time_difference_s": rec.time_difference_s,
                "match_score": rec.match_score,
                "review_status": rec.review_status.value if hasattr(rec.review_status, "value") else str(rec.review_status),
            }
            prov = rec.provenance.model_dump() if hasattr(rec.provenance, "model_dump") else dict(rec.provenance or {})
            record_models.append(
                HarmonisedRecordModel(
                    id=ensure_uuid(rec.harmonisation_id),
                    run_id=run_uuid,
                    match_status=rec_status,
                    modis_observation_id=ensure_uuid(rec.modis_observation_id) if rec.modis_observation_id else None,
                    viirs_observation_id=ensure_uuid(rec.viirs_observation_id) if rec.viirs_observation_id else None,
                    attributes=attrs,
                    provenance=prov,
                )
            )

        # Atomically persist candidates, records, and mark run succeeded
        db_run_repo.save_results(
            run_id=run_uuid,
            candidates=candidate_models,
            records=record_models,
            summary=summary.model_dump(),
        )
        db.commit()

        # Keep cache updated
        repo.save_run(summary, records, candidates, evaluation)

        return summary

    except Exception as exc:
        db.rollback()
        # Mark run as failed with sanitized error summary
        safe_err = sanitize_error_message(exc)
        db_run_repo.update_status(
            run_id=run_uuid,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            error_summary=safe_err,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing run execution failed: {safe_err}",
        )


@router.get("", response_model=List[ProcessingRunSummary])
def list_processing_runs(db: Session = Depends(get_db)) -> List[ProcessingRunSummary]:
    """List all processing runs from database."""
    db_run_repo = ProcessingRunRepository(db)
    db_runs = db_run_repo.list_all()
    if db_runs:
        return [run_model_to_summary(r) for r in db_runs]
    return repo.list_runs()


@router.get("/{run_id}", response_model=ProcessingRunSummary)
def get_processing_run(run_id: str, db: Session = Depends(get_db)) -> ProcessingRunSummary:
    """Retrieve summary metadata for a specific run."""
    db_run_repo = ProcessingRunRepository(db)
    db_run = db_run_repo.get(run_id)
    if db_run:
        return run_model_to_summary(db_run)

    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
        )
    return run


@router.get("/{run_id}/matches", response_model=List[HarmonisedRecord])
def get_run_matches(
    run_id: str,
    match_status: Optional[str] = Query(None, description="Comma-separated status: matched,ambiguous"),
    start_time: Optional[str] = Query(None, description="Filter observation time >= start_time"),
    end_time: Optional[str] = Query(None, description="Filter observation time <= end_time"),
    bbox: Optional[str] = Query(None, description="Bounding box min_lon,min_lat,max_lon,max_lat"),
    max_spatial_distance_m: Optional[float] = Query(None, ge=0.0),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[HarmonisedRecord]:
    """Retrieve matched and ambiguous records for a run with optional filtering."""
    db_run_repo = ProcessingRunRepository(db)
    db_run = db_run_repo.get(run_id)
    if db_run:
        if db_run.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run '{run_id}' has status '{db_run.status}'. Results are only available for succeeded runs.",
            )
    else:
        cached_run = repo.get_run(run_id)
        if not cached_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processing run '{run_id}' not found.",
            )
        if cached_run.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run '{run_id}' has status '{cached_run.status}'. Results are only available for succeeded runs.",
            )

    records = repo.get_run_records(run_id)
    matched_and_ambiguous = [
        r for r in records if r.match_status in [MatchStatus.MATCHED, MatchStatus.AMBIGUOUS]
    ]

    bbox_tuple = None
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) == 4:
                bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
        except ValueError:
            pass

    filtered, _ = ExporterService.filter_records(
        matched_and_ambiguous,
        match_status=match_status,
        start_time=start_time,
        end_time=end_time,
        bbox=bbox_tuple,
    )

    if max_spatial_distance_m is not None:
        filtered = [
            r for r in filtered
            if r.spatial_distance_m is not None and r.spatial_distance_m <= max_spatial_distance_m
        ]

    return filtered[offset : offset + limit]


@router.get("/{run_id}/unmatched", response_model=List[HarmonisedRecord])
def get_run_unmatched(
    run_id: str,
    sensor: Optional[str] = Query(None, description="Filter by sensor: MODIS or VIIRS"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[HarmonisedRecord]:
    """Retrieve preserved unmatched detections."""
    db_run_repo = ProcessingRunRepository(db)
    db_run = db_run_repo.get(run_id)
    if db_run:
        if db_run.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run '{run_id}' has status '{db_run.status}'. Results are only available for succeeded runs.",
            )
    else:
        cached_run = repo.get_run(run_id)
        if not cached_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processing run '{run_id}' not found.",
            )
        if cached_run.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run '{run_id}' has status '{cached_run.status}'. Results are only available for succeeded runs.",
            )

    records = repo.get_run_records(run_id)
    unmatched = [
        r for r in records
        if r.match_status in [MatchStatus.UNMATCHED_MODIS, MatchStatus.UNMATCHED_VIIRS]
    ]

    bbox_tuple = None
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) == 4:
                bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
        except ValueError:
            pass

    filtered, _ = ExporterService.filter_records(
        unmatched,
        sensor=sensor,
        start_time=start_time,
        end_time=end_time,
        bbox=bbox_tuple,
    )

    return filtered[offset : offset + limit]


@router.get("/{run_id}/summary", response_model=RunDetailedEvaluation)
def get_run_summary_evaluation(run_id: str) -> RunDetailedEvaluation:
    """Retrieve scientific evaluation metrics for a run (including 4 baselines & sensitivity grid)."""
    evaluation = repo.get_run_evaluation(run_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation metrics for run '{run_id}' not found.",
        )
    return evaluation


@router.post("/{run_id}/sensitivity", response_model=List[SensitivityGridPoint])
def run_custom_sensitivity(
    run_id: str,
    body: CustomSensitivityRequest,
    db: Session = Depends(get_db),
) -> List[SensitivityGridPoint]:
    """Run custom threshold sensitivity sweep for user-supplied distance and time arrays."""
    db_run_repo = ProcessingRunRepository(db)
    db_run = db_run_repo.get(run_id)
    run_obj = db_run or repo.get_run(run_id)

    if not run_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
        )

    inputs = run_obj.input_dataset_ids
    m_id = inputs.get("modis_dataset_id") if isinstance(inputs, dict) else inputs.modis_dataset_id
    v_id = inputs.get("viirs_dataset_id") if isinstance(inputs, dict) else inputs.viirs_dataset_id

    if not m_id or not v_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run lacks input dataset references.",
        )

    all_modis_obs = repo.get_observations(m_id)
    all_viirs_obs = repo.get_observations(v_id)

    params = run_obj.parameters
    if isinstance(params, dict):
        from backend.app.schemas.matching import MatchingParameters
        params = MatchingParameters(**params)

    q_filters = params.quality_filters
    m_eligible = StandardizationService.get_eligible_observations(
        all_modis_obs,
        include_warnings=q_filters.include_warnings,
        min_modis_confidence=q_filters.min_modis_confidence,
    )
    v_eligible = StandardizationService.get_eligible_observations(
        all_viirs_obs,
        include_warnings=q_filters.include_warnings,
        allowed_viirs_confidence_levels=q_filters.allowed_viirs_confidence_levels,
    )

    custom_grid = EvaluationService.run_threshold_sensitivity_grid(
        modis_obs=m_eligible,
        viirs_obs=v_eligible,
        base_params=params,
        distance_grid_m=body.distance_grid_m,
        time_grid_s=body.time_grid_s,
    )

    return custom_grid


@router.get("/{run_id}/export")
def export_run_results(
    run_id: str,
    format: str = Query("csv", pattern="^(csv|geojson)$"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter match_status"),
    sensor: Optional[str] = Query(None, description="Filter sensor"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Response:
    """
    Stream downloadable .csv or .geojson file with Content-Disposition filename
    containing run_id and timestamp (FR-19).
    Requires run status == 'succeeded'.
    """
    db_run_repo = ProcessingRunRepository(db)
    db_run = db_run_repo.get(run_id)
    if db_run:
        if db_run.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run '{run_id}' has status '{db_run.status}'. Results are only available for succeeded runs.",
            )
        run_summary = run_model_to_summary(db_run)
    else:
        cached_run = repo.get_run(run_id)
        if not cached_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processing run '{run_id}' not found.",
            )
        if cached_run.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run '{run_id}' has status '{cached_run.status}'. Results are only available for succeeded runs.",
            )
        run_summary = cached_run

    records = repo.get_run_records(run_id)

    bbox_tuple = None
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) == 4:
                bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
        except ValueError:
            pass

    filtered_records, filters_applied = ExporterService.filter_records(
        records=records,
        match_status=status_filter,
        sensor=sensor,
        start_time=start_time,
        end_time=end_time,
        bbox=bbox_tuple,
    )

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if format == "csv":
        csv_content = ExporterService.export_to_csv(run_summary, filtered_records, filters_applied)
        filename = f"harmonisation_{run_id}_{timestamp_str}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # GeoJSON format
    geojson_dict = ExporterService.export_to_geojson(run_summary, filtered_records, filters_applied)
    filename = f"harmonisation_{run_id}_{timestamp_str}.geojson"
    return Response(
        content=json.dumps(geojson_dict, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
