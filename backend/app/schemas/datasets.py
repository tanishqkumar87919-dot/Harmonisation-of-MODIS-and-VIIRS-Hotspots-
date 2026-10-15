"""Pydantic v2 schemas for Datasets, Ingestion, and Schema Quality Validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SensorType(str, Enum):
    MODIS = "MODIS"
    VIIRS = "VIIRS"


class RowQualityStatus(str, Enum):
    VALID = "valid"
    WARNING = "warning"
    REJECTED = "rejected"


class SchemaMappingPreviewItem(BaseModel):
    source_column: str
    internal_field: str
    sample_raw_value: str
    sample_normalized_value: str
    unit_or_note: str

    model_config = ConfigDict(from_attributes=True)


class DatasetValidationReportSchema(BaseModel):
    """Validation report generated during Stage A inspection & Stage C QC."""
    dataset_id: str
    sensor: SensorType
    product_name: str
    product_version: str
    total_input_rows: int
    valid_count: int
    warning_count: int
    rejected_count: int
    duplicate_row_count: int
    missing_coordinate_count: int
    out_of_range_coordinate_count: int
    malformed_timestamp_count: int
    missing_required_field_count: int
    rejection_reasons: Dict[str, int] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    schema_mapping_preview: List[SchemaMappingPreviewItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
ValidationReport = DatasetValidationReportSchema


class DatasetRecordSchema(BaseModel):
    """Dataset metadata record adhering to docs/04_DATA_SOURCES_AND_DICTIONARY.md."""
    id: str
    sensor: SensorType
    product_name: str
    product_version: str
    source_uri: str
    retrieved_at: str
    checksum: str
    total_rows: int
    valid_rows: int
    warning_rows: int
    rejected_rows: int
    min_time_utc: Optional[str] = None
    max_time_utc: Optional[str] = None
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    is_test_fixture: bool = False

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
DatasetRecord = DatasetRecordSchema


class DatasetUploadMetadata(BaseModel):
    sensor: Optional[SensorType] = None
    product_name: Optional[str] = None
    product_version: Optional[str] = None
    source_uri: Optional[str] = None
