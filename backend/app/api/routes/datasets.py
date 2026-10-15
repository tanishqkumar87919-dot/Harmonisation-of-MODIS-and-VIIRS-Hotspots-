"""Dataset endpoints for validation, upload, inspection, and deletion."""

from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.app.schemas.common import SensorType
from backend.app.schemas.dataset import DatasetRecord, ValidationReport
from backend.app.services.ingestion import IngestionError, IngestionService
from backend.app.services.repository import repo
from backend.app.services.standardization import StandardizationService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/validate", response_model=ValidationReport, status_code=status.HTTP_201_CREATED)
async def validate_and_upload_dataset(
    file: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    product_version: Optional[str] = Form(None),
    sensor: Optional[str] = Form(None),
) -> ValidationReport:
    """
    Validate uploaded satellite CSV file.
    Performs schema validation, coordinate checks, duplicate detection, and standardization.
    """
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    sensor_enum = None
    if sensor:
        try:
            sensor_enum = SensorType(sensor.upper())
        except ValueError:
            pass

    try:
        report, dataset_rec, df = IngestionService.inspect_and_validate(
            file_content=content,
            source_uri=file.filename or "uploaded.csv",
            explicit_sensor=sensor_enum,
            product_name=product_name,
            product_version=product_version,
        )
    except IngestionError as ie:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ie),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal ingestion error: {str(exc)}",
        )

    # Standardize records
    observations = StandardizationService.standardize_records(df, dataset_rec)

    # Persist in repository
    repo.save_dataset(dataset_rec, observations, raw_bytes=content)

    return report


@router.get("", response_model=List[DatasetRecord])
def list_datasets() -> List[DatasetRecord]:
    """Retrieve all ingested satellite datasets."""
    return repo.list_datasets()


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: str) -> None:
    """Delete a dataset and its observations by ID."""
    deleted = repo.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
