"""Pydantic v2 schema for Standardized Active-Fire Observations (17 Internal Fields)."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.datasets import RowQualityStatus, SensorType


class StandardizedObservationSchema(BaseModel):
    """
    Standardized observation containing all 17 internal fields defined in:
    docs/04_DATA_SOURCES_AND_DICTIONARY.md (Section 4)
    Strictly preserves raw measurements, sensor physics, and source provenance.
    """

    # 17 Internal Fields
    observation_id: str = Field(description="Unique internal observation UUID")
    dataset_id: str = Field(description="Parent dataset identifier")
    source_record_id: str = Field(description="Stable source record identifier or row index")
    source_sensor: SensorType = Field(description="MODIS or VIIRS")
    platform: str = Field(description="Satellite platform name (Terra, Aqua, Suomi-NPP, NOAA-20)")
    product_name: str = Field(description="Exact product name (e.g. MOD14, VNP14IMGTDL)")
    product_version: str = Field(description="Product collection version (e.g. C6.1, v1.0)")
    observation_time_utc: str = Field(description="Timezone-aware ISO-8601 UTC observation timestamp")
    latitude: float = Field(ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    confidence_raw: Optional[Union[str, int, float]] = Field(
        default=None,
        description="Preserved raw confidence representation (0-100 for MODIS, categorical string for VIIRS)",
    )
    frp_raw: Optional[float] = Field(
        default=None,
        description="Preserved raw Fire Radiative Power in MW without cross-sensor conversions",
    )
    frp_unit: Optional[str] = Field(default="MW", description="Measurement unit of FRP")
    scan_raw: Optional[float] = Field(default=None, description="Along-scan footprint dimension in km")
    track_raw: Optional[float] = Field(default=None, description="Along-track footprint dimension in km")
    quality_flags_raw: Optional[Union[Dict[str, Any], str]] = Field(
        default_factory=dict,
        description="Dictionary of sensor-specific flags (daynight, brightness channels, etc.)",
    )
    ingestion_run_id: str = Field(description="Traceable ingestion batch ID")

    # Audit & Quality Verification
    row_quality_status: RowQualityStatus = Field(
        default=RowQualityStatus.VALID,
        description="Quality status: valid, warning, or rejected",
    )
    quality_notes: List[str] = Field(
        default_factory=list,
        description="List of specific quality audit notes or warnings",
    )
    raw_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete unmodified original row key-value pairs for full auditability",
    )

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
StandardizedObservation = StandardizedObservationSchema
