"""Dataset endpoints for validation, upload, inspection, and deletion."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.db.models import DatasetModel, ObservationModel
from backend.app.db.repositories import DatasetRepository, ObservationRepository
from backend.app.db.session import get_db
from backend.app.schemas.common import RowQualityStatus
from backend.app.schemas.datasets import (
    DatasetRecordSchema,
    DatasetValidationReportSchema,
    SensorType,
)
from backend.app.schemas.observations import StandardizedObservationSchema
from backend.app.services.ingestion import IngestionError, IngestionService
from backend.app.services.repository import repo
from backend.app.services.standardization import StandardizationService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


class DatasetDetailResponse(BaseModel):
    dataset: DatasetRecordSchema
    observations: List[StandardizedObservationSchema]
    total_observations: int
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)


def model_to_dataset_schema(m: DatasetModel, obs_count: int = 0) -> DatasetRecordSchema:
    meta = m.metadata_json or {}
    sensor_enum = SensorType.MODIS if m.sensor == "MODIS" else SensorType.VIIRS
    return DatasetRecordSchema(
        id=meta.get("external_id") or str(m.id),
        sensor=sensor_enum,
        product_name=m.product_name,
        product_version=m.product_version,
        source_uri=m.source_uri or "",
        retrieved_at=m.retrieved_at.isoformat() if m.retrieved_at else "",
        checksum=m.checksum or "",
        total_rows=meta.get("total_rows", obs_count),
        valid_rows=meta.get("valid_rows", obs_count),
        warning_rows=meta.get("warning_rows", 0),
        rejected_rows=meta.get("rejected_rows", 0),
        is_test_fixture=meta.get("is_test_fixture", False),
    )


def obs_model_to_schema(obs: ObservationModel) -> StandardizedObservationSchema:
    sensor_enum = SensorType.MODIS if obs.sensor == "MODIS" else SensorType.VIIRS
    raw = obs.raw_fields or {}
    conf_val: Any = obs.confidence_raw
    if obs.sensor == "MODIS" and conf_val is not None:
        try:
            conf_val = int(float(conf_val))
        except ValueError:
            pass

    return StandardizedObservationSchema(
        observation_id=str(obs.id),
        dataset_id=str(obs.dataset_id),
        source_record_id=obs.source_record_id,
        source_sensor=sensor_enum,
        platform=raw.get("platform", "Unknown"),
        product_name=raw.get("product_name", "Unknown"),
        product_version=raw.get("product_version", "1.0"),
        observation_time_utc=obs.observed_at.isoformat() if obs.observed_at else "1970-01-01T00:00:00Z",
        latitude=obs.latitude if obs.latitude is not None else 0.0,
        longitude=obs.longitude if obs.longitude is not None else 0.0,
        confidence_raw=conf_val,
        frp_raw=obs.frp_raw,
        frp_unit=obs.frp_unit,
        scan_raw=raw.get("scan"),
        track_raw=raw.get("track"),
        quality_flags_raw=raw.get("quality_flags"),
        ingestion_run_id=raw.get("ingestion_run_id", "ingest-db"),
        row_quality_status=RowQualityStatus(obs.quality_status),
        quality_notes=obs.quality_notes or [],
        raw_fields=raw,
    )


@router.post("/validate", response_model=DatasetValidationReportSchema, status_code=status.HTTP_201_CREATED)
async def validate_and_upload_dataset(
    file: UploadFile = File(...),
    sensor: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    product_version: Optional[str] = Form(None),
    source_uri: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> DatasetValidationReportSchema:
    """
    Validate uploaded satellite CSV file.
    Executes:
    - Stage A: File extension, size limit, SHA-256 checksum, raw string CSV parsing, required columns.
    - Stage B: 17 internal fields standardization & source provenance.
    - Stage C: Row-level Quality Control (valid, warning, rejected).
    Persists data atomically in both relational database and cache store.
    """
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    filename = file.filename or "uploaded.csv"

    # Stage A Parsing & Validation
    try:
        df_raw, content_bytes, checksum = IngestionService.parse_raw_csv(content, filename)
        renamed_df, _ = IngestionService.normalize_column_names(df_raw)
        IngestionService.verify_required_columns(renamed_df)
    except IngestionError as ie:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ie),
        )

    # Detect sensor
    sensor_enum = IngestionService.detect_sensor(renamed_df, sensor)

    # Product metadata defaults
    prod_name = product_name or (
        "MOD14_Terra_Collection_6_1" if sensor_enum == SensorType.MODIS else "VNP14IMGTDL_NPP_Collection_1"
    )
    prod_ver = product_version or ("C6.1" if sensor_enum == SensorType.MODIS else "v1.0")
    dataset_uuid = f"ds-{uuid.uuid4().hex[:12]}"
    ingest_run_id = f"ingest-{uuid.uuid4().hex[:8]}"

    # Stages B & C: Standardization & QC
    report, dataset_record, observations = StandardizationService.process_and_standardize(
        df_raw=renamed_df,
        dataset_id=dataset_uuid,
        sensor=sensor_enum,
        product_name=prod_name,
        product_version=prod_ver,
        source_uri=source_uri or filename,
        checksum=checksum,
        ingestion_run_id=ingest_run_id,
    )

    # Persist in Database
    meta_dict = {
        "external_id": dataset_uuid,
        "total_rows": dataset_record.total_rows,
        "valid_rows": dataset_record.valid_rows,
        "warning_rows": dataset_record.warning_rows,
        "rejected_rows": dataset_record.rejected_rows,
        "is_test_fixture": dataset_record.is_test_fixture,
    }
    dataset_record_for_db = dataset_record.model_copy()
    dataset_record_for_db.metadata_json = meta_dict

    db_ds_repo = DatasetRepository(db)
    db_ds_repo.create(dataset_record_for_db, observations, raw_bytes=content_bytes)
    db.commit()

    # Also keep in-memory cache synchronized
    repo.save_dataset(dataset_record, observations, raw_bytes=content_bytes)

    return report


@router.get("", response_model=List[DatasetRecordSchema])
def list_datasets(db: Session = Depends(get_db)) -> List[DatasetRecordSchema]:
    """Retrieve all ingested satellite datasets from database."""
    db_ds_repo = DatasetRepository(db)
    db_models = db_ds_repo.list_all()
    if db_models:
        obs_repo = ObservationRepository(db)
        return [model_to_dataset_schema(m, obs_repo.count_by_dataset(m.id)) for m in db_models]
    return repo.list_datasets()


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(
    dataset_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> DatasetDetailResponse:
    """Retrieve single dataset metadata and paginated standardized observations."""
    db_ds_repo = DatasetRepository(db)
    db_obs_repo = ObservationRepository(db)

    db_ds = db_ds_repo.get(dataset_id)
    if db_ds:
        total = db_obs_repo.count_by_dataset(db_ds.id)
        obs_models = db_obs_repo.get_by_dataset(db_ds.id, limit=limit, offset=offset)
        schema_obs = [obs_model_to_schema(o) for o in obs_models]
        return DatasetDetailResponse(
            dataset=model_to_dataset_schema(db_ds, total),
            observations=schema_obs,
            total_observations=total,
            limit=limit,
            offset=offset,
        )

    # Fallback to cache
    dataset = repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )

    all_obs = repo.get_observations(dataset_id)
    paginated_obs = all_obs[offset : offset + limit]

    return DatasetDetailResponse(
        dataset=dataset,
        observations=paginated_obs,
        total_observations=len(all_obs),
        limit=limit,
        offset=offset,
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a dataset and its observations by ID."""
    db_ds_repo = DatasetRepository(db)
    db_deleted = db_ds_repo.delete(dataset_id)
    if db_deleted:
        db.commit()

    cache_deleted = repo.delete_dataset(dataset_id)
    if not db_deleted and not cache_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
