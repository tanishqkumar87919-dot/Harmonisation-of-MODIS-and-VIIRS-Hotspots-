"""Processing run endpoints for harmonisation execution, records inspection, sensitivity, and exports."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query, Response, status

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


@router.post("", response_model=ProcessingRunSummary, status_code=status.HTTP_201_CREATED)
def create_processing_run(payload: RunCreateRequest) -> ProcessingRunSummary:
    """
    Launch a reproducible harmonisation run linking MODIS and VIIRS datasets.
    """
    modis_ds = repo.get_dataset(payload.modis_dataset_id)
    if not modis_ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MODIS dataset '{payload.modis_dataset_id}' not found.",
        )

    viirs_ds = repo.get_dataset(payload.viirs_dataset_id)
    if not viirs_ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VIIRS dataset '{payload.viirs_dataset_id}' not found.",
        )

    all_modis_obs = repo.get_observations(payload.modis_dataset_id)
    all_viirs_obs = repo.get_observations(payload.viirs_dataset_id)

    # Filter eligible observations per configured quality filters
    q_filters = payload.parameters.quality_filters
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

    run_id = f"run-{uuid.uuid4().hex[:12]}"

    engine_result = MatchingEngineService.run_harmonisation(
        run_id=run_id,
        modis_observations=eligible_modis,
        viirs_observations=eligible_viirs,
        parameters=payload.parameters,
        modis_input_count=modis_ds.total_rows,
        viirs_input_count=viirs_ds.total_rows,
        modis_warning_count=modis_ds.warning_rows,
        viirs_warning_count=viirs_ds.warning_rows,
        modis_rejected_count=modis_ds.rejected_rows,
        viirs_rejected_count=viirs_ds.rejected_rows,
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

    repo.save_run(summary, records, candidates, evaluation)

    return summary


@router.get("", response_model=List[ProcessingRunSummary])
def list_processing_runs() -> List[ProcessingRunSummary]:
    """List all processing runs."""
    return repo.list_runs()


@router.get("/{run_id}", response_model=ProcessingRunSummary)
def get_processing_run(run_id: str) -> ProcessingRunSummary:
    """Retrieve summary metadata for a specific run."""
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
) -> List[HarmonisedRecord]:
    """Retrieve matched and ambiguous records for a run with optional filtering."""
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
        )

    records = repo.get_run_records(run_id)
    matched_and_ambiguous = [
        r for r in records if r.match_status in [MatchStatus.MATCHED, MatchStatus.AMBIGUOUS]
    ]

    # Parse bbox if provided
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
) -> List[HarmonisedRecord]:
    """Retrieve preserved unmatched detections."""
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
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
) -> List[SensitivityGridPoint]:
    """Run custom threshold sensitivity sweep for user-supplied distance and time arrays."""
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
        )

    m_id = run.input_dataset_ids.modis_dataset_id
    v_id = run.input_dataset_ids.viirs_dataset_id

    if not m_id or not v_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run lacks input dataset references.",
        )

    all_modis_obs = repo.get_observations(m_id)
    all_viirs_obs = repo.get_observations(v_id)

    q_filters = run.parameters.quality_filters
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
        base_params=run.parameters,
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
) -> Response:
    """
    Stream downloadable .csv or .geojson file with Content-Disposition filename
    containing run_id and timestamp (FR-19).
    """
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
        )

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
        csv_content = ExporterService.export_to_csv(run, filtered_records, filters_applied)
        filename = f"harmonisation_{run_id}_{timestamp_str}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # GeoJSON format
    geojson_dict = ExporterService.export_to_geojson(run, filtered_records, filters_applied)
    filename = f"harmonisation_{run_id}_{timestamp_str}.geojson"
    return Response(
        content=json.dumps(geojson_dict, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
