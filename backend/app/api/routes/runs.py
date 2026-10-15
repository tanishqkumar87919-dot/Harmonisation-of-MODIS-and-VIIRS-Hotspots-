"""Processing run endpoints for harmonisation execution, records inspection, and exports."""

import io
import json
import uuid
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Response, status

from backend.app.schemas.common import MatchStatus, SensorType
from backend.app.schemas.matching import HarmonisedRecord, RunCreateRequest
from backend.app.schemas.run import ProcessingRunSummary, RunDetailedEvaluation
from backend.app.services.evaluation import EvaluationService
from backend.app.services.matching import MatchingEngine
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

    records, candidates, summary = MatchingEngine.execute_matching_run(
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
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    max_spatial_distance_m: Optional[float] = Query(None, ge=0.0),
) -> List[HarmonisedRecord]:
    """Retrieve matched and ambiguous records for a run."""
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
        )

    records = repo.get_run_records(run_id)
    # Include matched and ambiguous
    filtered = [r for r in records if r.match_status in [MatchStatus.MATCHED, MatchStatus.AMBIGUOUS]]

    if max_spatial_distance_m is not None:
        filtered = [
            r for r in filtered
            if r.spatial_distance_m is not None and r.spatial_distance_m <= max_spatial_distance_m
        ]

    return filtered[offset : offset + limit]


@router.get("/{run_id}/unmatched", response_model=List[HarmonisedRecord])
def get_run_unmatched(
    run_id: str,
    sensor: Optional[str] = Query(None),
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

    if sensor:
        sensor_clean = sensor.upper().strip()
        if "MODIS" in sensor_clean:
            unmatched = [r for r in unmatched if r.match_status == MatchStatus.UNMATCHED_MODIS]
        elif "VIIRS" in sensor_clean:
            unmatched = [r for r in unmatched if r.match_status == MatchStatus.UNMATCHED_VIIRS]

    return unmatched[offset : offset + limit]


@router.get("/{run_id}/summary", response_model=RunDetailedEvaluation)
def get_run_summary_evaluation(run_id: str) -> RunDetailedEvaluation:
    """Retrieve scientific evaluation metrics for a run."""
    evaluation = repo.get_run_evaluation(run_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation metrics for run '{run_id}' not found.",
        )
    return evaluation


@router.get("/{run_id}/export")
def export_run_results(
    run_id: str,
    format: str = Query("csv", pattern="^(csv|geojson)$"),
    status_filter: Optional[str] = Query(None, alias="status"),
) -> Response:
    """
    Export harmonised observations in CSV or GeoJSON format.
    Preserves all provenance and sensor-specific attributes.
    """
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing run '{run_id}' not found.",
        )

    records = repo.get_run_records(run_id)

    if status_filter:
        statuses = [s.strip().lower() for s in status_filter.split(",")]
        records = [r for r in records if r.match_status.value.lower() in statuses]

    if format == "csv":
        rows = []
        for r in records:
            m = r.modis_observation
            v = r.viirs_observation
            rows.append({
                "harmonisation_id": r.harmonisation_id,
                "run_id": r.run_id,
                "match_status": r.match_status.value,
                "spatial_distance_m": r.spatial_distance_m,
                "time_difference_s": r.time_difference_s,
                "match_score": r.match_score,
                "matching_method_version": r.matching_method_version,
                # MODIS attributes
                "modis_observation_id": r.modis_observation_id,
                "modis_source_record_id": r.provenance.modis_source_record_id,
                "modis_latitude": m.latitude if m else None,
                "modis_longitude": m.longitude if m else None,
                "modis_time_utc": m.observation_time_utc if m else None,
                "modis_confidence_raw": m.confidence_raw if m else None,
                "modis_frp_mw": m.frp_raw if m else None,
                "modis_platform": m.platform if m else None,
                # VIIRS attributes
                "viirs_observation_id": r.viirs_observation_id,
                "viirs_source_record_id": r.provenance.viirs_source_record_id,
                "viirs_latitude": v.latitude if v else None,
                "viirs_longitude": v.longitude if v else None,
                "viirs_time_utc": v.observation_time_utc if v else None,
                "viirs_confidence_raw": v.confidence_raw if v else None,
                "viirs_frp_mw": v.frp_raw if v else None,
                "viirs_platform": v.platform if v else None,
                # Provenance notes
                "candidate_count": r.provenance.candidate_count,
                "decision_reason": r.provenance.decision_reason,
            })

        df_export = pd.DataFrame(rows)
        csv_buffer = io.StringIO()
        df_export.to_csv(csv_buffer, index=False)
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=harmonisation_{run_id}.csv"},
        )

    # GeoJSON format
    features = []
    for r in records:
        m = r.modis_observation
        v = r.viirs_observation
        # Anchor coordinate: use VIIRS (finer resolution) if present, else MODIS
        coord = [v.longitude, v.latitude] if v else ([m.longitude, m.latitude] if m else [0.0, 0.0])

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coord,
            },
            "properties": {
                "harmonisation_id": r.harmonisation_id,
                "match_status": r.match_status.value,
                "spatial_distance_m": r.spatial_distance_m,
                "time_difference_s": r.time_difference_s,
                "match_score": r.match_score,
                "modis_observation_id": r.modis_observation_id,
                "viirs_observation_id": r.viirs_observation_id,
                "modis_confidence": m.confidence_raw if m else None,
                "viirs_confidence": v.confidence_raw if v else None,
                "modis_frp_mw": m.frp_raw if m else None,
                "viirs_frp_mw": v.frp_raw if v else None,
            },
        }
        features.append(feature)

    geojson_doc = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "run_id": run_id,
            "method_version": run.method_version,
            "total_features": len(features),
        },
    }

    return Response(
        content=json.dumps(geojson_doc, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": f"attachment; filename=harmonisation_{run_id}.geojson"},
    )
