"""Pydantic model for Standardized Observation across MODIS and VIIRS."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from backend.app.schemas.common import RowQualityStatus, SensorType


class StandardizedObservation(BaseModel):
    """
    Standardized Active-Fire Observation.
    Contains all 17 internal fields defined in docs/04_DATA_SOURCES_AND_DICTIONARY.md
    while preserving original sensor physics, raw confidence scales, and provenance.
    """
    # 17 Internal Fields
    observation_id: str
    dataset_id: str
    source_record_id: str
    source_sensor: SensorType
    platform: str
    product_name: str
    product_version: str
    observation_time_utc: str  # ISO 8601 UTC
    latitude: float            # [-90.0, 90.0]
    longitude: float           # [-180.0, 180.0]
    confidence_raw: Optional[Union[str, int, float]] = None
    frp_raw: Optional[float] = None
    frp_unit: Optional[str] = None
    scan_raw: Optional[float] = None
    track_raw: Optional[float] = None
    quality_flags_raw: Optional[Union[Dict[str, Any], str]] = None
    ingestion_run_id: str

    # Quality & Provenance Audit
    row_quality_status: RowQualityStatus = RowQualityStatus.VALID
    quality_notes: List[str] = Field(default_factory=list)
    raw_fields: Dict[str, Any] = Field(default_factory=dict)
