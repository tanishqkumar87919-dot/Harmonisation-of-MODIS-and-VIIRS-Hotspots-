"""Stage A: Data inspection, file validation, and schema ingestion service."""

import hashlib
import io
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from backend.app.config import settings
from backend.app.schemas.datasets import (
    DatasetRecordSchema,
    DatasetValidationReportSchema,
    SchemaMappingPreviewItem,
    SensorType,
)


class IngestionError(Exception):
    """Raised when an uploaded file cannot be parsed or lacks critical metadata."""
    pass


class IngestionService:
    """
    Stage A Ingestion:
    - File extension and size constraints (NFR-05, FR-01, FR-03).
    - SHA-256 cryptographic checksum calculation (04_DATA_SOURCES_AND_DICTIONARY.md Section 7).
    - Raw string CSV parsing (preserving original precision and preventing numeric coercion).
    - Schema validation for required coordinate and timestamp columns (FR-05).
    """

    @staticmethod
    def compute_checksum(content_bytes: bytes) -> str:
        """Compute SHA-256 digest of raw file content."""
        return hashlib.sha256(content_bytes).hexdigest()

    @classmethod
    def validate_file_metadata(cls, filename: str, content_bytes: bytes) -> None:
        """Enforce upload security, extension, and size limits."""
        if not content_bytes or len(content_bytes) == 0:
            raise IngestionError("The uploaded file is empty (0 bytes).")

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content_bytes) > max_bytes:
            raise IngestionError(
                f"File size ({len(content_bytes) / (1024 * 1024):.2f}MB) exceeds "
                f"configured limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if not any(filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
            raise IngestionError(
                f"Unsupported file extension '{filename}'. Allowed extensions: {settings.ALLOWED_EXTENSIONS}."
            )

    @classmethod
    def detect_sensor(
        cls, df: pd.DataFrame, explicit_sensor: Optional[Union[SensorType, str]] = None
    ) -> SensorType:
        """Infer sensor type from columns, instrument metadata, or explicit hint."""
        if explicit_sensor:
            if isinstance(explicit_sensor, SensorType):
                return explicit_sensor
            sensor_str = str(explicit_sensor).upper()
            if "VIIRS" in sensor_str:
                return SensorType.VIIRS
            if "MODIS" in sensor_str:
                return SensorType.MODIS

        cols_lower = {str(c).strip().lower() for c in df.columns}

        # Check VIIRS specific columns
        if any(c in cols_lower for c in ["bright_ti4", "bright_ti5"]):
            return SensorType.VIIRS

        # Check MODIS specific columns
        if "bright_t31" in cols_lower:
            return SensorType.MODIS

        # Check instrument / satellite columns in data
        for col in ["instrument", "satellite"]:
            if col in cols_lower:
                vals = df[col].dropna().astype(str).str.upper().unique()
                if any("VIIRS" in v for v in vals):
                    return SensorType.VIIRS
                if any("MODIS" in v or "TERRA" in v or "AQUA" in v for v in vals):
                    return SensorType.MODIS

        if "confidence" in cols_lower:
            sample_vals = df["confidence"].dropna().astype(str).str.lower().head(20).tolist()
            if any(v in ["l", "n", "h", "low", "nominal", "high"] for v in sample_vals):
                return SensorType.VIIRS

        return SensorType.MODIS

    @classmethod
    def normalize_column_names(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Normalize DataFrame column names to lower case and detect standard mappings.
        Returns cleaned DataFrame and mapping dict (normalized_name -> original_name).
        """
        original_to_norm = {}
        for c in df.columns:
            cleaned = str(c).strip()
            norm = cleaned.lower()
            if norm in ["lat", "latitude_deg", "y"]:
                norm = "latitude"
            elif norm in ["lon", "long", "longitude_deg", "x"]:
                norm = "longitude"
            elif norm in ["date", "acqdate"]:
                norm = "acq_date"
            elif norm in ["time", "acqtime"]:
                norm = "acq_time"
            elif norm in ["timestamp", "datetime", "utc_time"]:
                norm = "observation_time_utc"
            original_to_norm[c] = norm

        reversed_mapping = {v: k for k, v in original_to_norm.items()}
        renamed_df = df.rename(columns=original_to_norm)
        return renamed_df, reversed_mapping

    @classmethod
    def parse_raw_csv(
        cls,
        file_content: Union[bytes, str, io.StringIO, io.BytesIO],
        filename: str = "uploaded.csv",
    ) -> Tuple[pd.DataFrame, bytes, str]:
        """
        Parse CSV content using dtype=str to preserve exact raw strings without coercion.
        """
        if isinstance(file_content, bytes):
            content_bytes = file_content
            stream = io.BytesIO(content_bytes)
        elif isinstance(file_content, str):
            content_bytes = file_content.encode("utf-8")
            stream = io.StringIO(file_content)
        elif isinstance(file_content, io.BytesIO):
            content_bytes = file_content.getvalue()
            stream = file_content
            stream.seek(0)
        elif isinstance(file_content, io.StringIO):
            content_bytes = file_content.getvalue().encode("utf-8")
            stream = file_content
            stream.seek(0)
        else:
            raise IngestionError("Unsupported file stream type.")

        cls.validate_file_metadata(filename, content_bytes)
        checksum = cls.compute_checksum(content_bytes)

        try:
            df = pd.read_csv(stream, dtype=str, keep_default_na=False)
        except pd.errors.EmptyDataError:
            raise IngestionError("The uploaded CSV file is empty (0 observation rows).")
        except Exception as e:
            raise IngestionError(f"Failed to parse CSV file: {str(e)}")

        if len(df) == 0:
            raise IngestionError("The uploaded CSV contains 0 observation rows.")

        return df, content_bytes, checksum

    @classmethod
    def verify_required_columns(cls, df: pd.DataFrame) -> None:
        """
        Verify required coordinate and timestamp columns exist (FR-03, FR-05).
        """
        missing_cols: List[str] = []
        if "latitude" not in df.columns:
            missing_cols.append("latitude")
        if "longitude" not in df.columns:
            missing_cols.append("longitude")

        has_timestamp = "observation_time_utc" in df.columns or (
            "acq_date" in df.columns
        )
        if not has_timestamp:
            missing_cols.append("acq_date (or observation_time_utc)")

        if missing_cols:
            raise IngestionError(
                f"CSV lacks required columns: {', '.join(missing_cols)}. "
                "Active-fire files must include latitude, longitude, and acquisition timestamp per Data Dictionary."
            )

    @classmethod
    def inspect_and_validate(
        cls,
        file_content: Union[bytes, str, io.StringIO, io.BytesIO],
        dataset_id: Optional[str] = None,
        source_uri: str = "uploaded_file.csv",
        explicit_sensor: Optional[Union[SensorType, str]] = None,
        product_name: Optional[str] = None,
        product_version: Optional[str] = None,
        is_test_fixture: bool = False,
    ):
        """Convenience wrapper combining Stages A, B, and C."""
        from backend.app.services.standardization import StandardizationService

        df_raw, content_bytes, checksum = cls.parse_raw_csv(file_content, source_uri)
        renamed_df, _ = cls.normalize_column_names(df_raw)
        cls.verify_required_columns(renamed_df)

        sensor = cls.detect_sensor(renamed_df, explicit_sensor)
        prod_name = product_name or (
            "MOD14_Terra_Collection_6_1" if sensor == SensorType.MODIS else "VNP14IMGTDL_NPP_Collection_1"
        )
        prod_ver = product_version or ("C6.1" if sensor == SensorType.MODIS else "v1.0")
        ds_id = dataset_id or f"ds-{uuid.uuid4().hex[:12]}"
        ingest_id = f"ingest-{uuid.uuid4().hex[:8]}"

        report, dataset_rec, observations = StandardizationService.process_and_standardize(
            df_raw=renamed_df,
            dataset_id=ds_id,
            sensor=sensor,
            product_name=prod_name,
            product_version=prod_ver,
            source_uri=source_uri,
            checksum=checksum,
            ingestion_run_id=ingest_id,
            is_test_fixture=is_test_fixture,
        )
        return report, dataset_rec, renamed_df

