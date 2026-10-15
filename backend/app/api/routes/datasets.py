"""Dataset endpoints for validation, upload, inspection, and deletion."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict

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


@router.post("/validate", response_model=DatasetValidationReportSchema, status_code=status.HTTP_201_CREATED)
async def validate_and_upload_dataset(
    file: UploadFile = File(...),
    sensor: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    product_version: Optional[str] = Form(None),
    source_uri: Optional[str] = Form(None),
) -> DatasetValidationReportSchema:
    """
    Validate uploaded satellite CSV file.
    Executes:
    - Stage A: File extension, size limit, SHA-256 checksum, raw string CSV parsing, required columns.
    - Stage B: 17 internal fields standardization & source provenance.
    - Stage C: Row-level Quality Control (valid, warning, rejected).
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

    # Persist in repository
    repo.save_dataset(dataset_record, observations, raw_bytes=content_bytes)

    return report


@router.get("", response_model=List[DatasetRecordSchema])
def list_datasets() -> List[DatasetRecordSchema]:
    """Retrieve all ingested satellite datasets."""
    return repo.list_datasets()


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(
    dataset_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> DatasetDetailResponse:
    """Retrieve single dataset metadata and paginated standardized observations."""
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
def delete_dataset(dataset_id: str) -> None:
    """Delete a dataset and its observations by ID."""
    deleted = repo.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
