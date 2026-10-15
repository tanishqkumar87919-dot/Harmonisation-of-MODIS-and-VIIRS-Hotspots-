"""Data inspection, validation, and ingestion service for MODIS and VIIRS active-fire files."""

import hashlib
import io
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

import numpy as np
import pandas as pd

from backend.app.schemas.common import RowQualityStatus, SensorType
from backend.app.schemas.dataset import (
    DatasetRecord,
    SchemaMappingPreviewItem,
    ValidationReport,
)


class IngestionError(Exception):
    """Raised when an uploaded file cannot be parsed or lacks critical metadata."""
    pass


class IngestionService:
    """
    Ingests and inspects raw satellite active-fire observation files (CSV).
    Enforces scientific integrity:
    - Never fabricates coordinates or dates.
    - Preserves raw input values.
    - Accurately reports valid, warning, and rejected counts with specific reasons.
    """

    SUPPORTED_SENSORS = [SensorType.MODIS, SensorType.VIIRS]

    @staticmethod
    def compute_checksum(content_bytes: bytes) -> str:
        """Calculate SHA-256 digest of input content."""
        return hashlib.sha256(content_bytes).hexdigest()

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

        # Fallback heuristic: check confidence type (VIIRS is often l/n/h string, MODIS is 0-100)
        if "confidence" in cols_lower:
            sample_vals = df["confidence"].dropna().astype(str).str.lower().head(20).tolist()
            if any(v in ["l", "n", "h", "low", "nominal", "high"] for v in sample_vals):
                return SensorType.VIIRS

        # Default to MODIS if ambiguous
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
            # Standard aliases
            if norm in ["lat", "latitude_deg", "y"]:
                norm = "latitude"
            elif norm in ["lon", "long", "longitude_deg", "x"]:
                norm = "longitude"
            elif norm in ["date", "acqdate"]:
                norm = "acq_date"
            elif norm in ["time", "acqtime"]:
                norm = "acq_time"
            original_to_norm[c] = norm

        reversed_mapping = {v: k for k, v in original_to_norm.items()}
        renamed_df = df.rename(columns=original_to_norm)
        return renamed_df, reversed_mapping

    @classmethod
    def parse_datetime(cls, date_val: Any, time_val: Any = None) -> Optional[datetime]:
        """
        Parse date and time into UTC datetime.
        Supports standard FIRMS format:
        date: '2023-05-01' or '2023/05/01'
        time: 430, '0430', '04:30', '04:30:00'
        """
        if pd.isna(date_val) or date_val is None:
            return None

        date_str = str(date_val).strip()
        time_str = "" if time_val is None or pd.isna(time_val) else str(time_val).strip()

        # Handle compound ISO datetime in single date field
        if "T" in date_str or (" " in date_str and len(date_str) > 10):
            try:
                dt = pd.to_datetime(date_str, utc=True)
                return dt.to_pydatetime()
            except Exception:
                pass

        # Parse acq_time: e.g. 430 -> "0430", 1245 -> "1245"
        if time_str.endswith(".0"):
            time_str = time_str[:-2]
        if ":" in time_str:
            parts = time_str.split(":")
            hour = parts[0].zfill(2)
            minute = parts[1].zfill(2) if len(parts) > 1 else "00"
            second = parts[2].zfill(2) if len(parts) > 2 else "00"
            clean_time = f"{hour}:{minute}:{second}"
        elif len(time_str) > 0 and time_str.isdigit():
            padded = time_str.zfill(4)
            clean_time = f"{padded[:2]}:{padded[2:4]}:00"
        else:
            clean_time = "00:00:00"

        combined = f"{date_str} {clean_time}"
        try:
            dt = pd.to_datetime(combined, utc=True)
            return dt.to_pydatetime()
        except Exception:
            return None

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
    ) -> Tuple[ValidationReport, DatasetRecord, pd.DataFrame]:
        """
        Inspect raw file, validate schema and coordinate constraints, and produce
        the scientific ValidationReport and DatasetRecord.
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

        checksum = cls.compute_checksum(content_bytes)
        dataset_uuid = dataset_id or f"ds-{uuid.uuid4().hex[:12]}"

        # Read CSV
        try:
            df_raw = pd.read_csv(stream)
        except pd.errors.EmptyDataError:
            raise IngestionError("The uploaded CSV file is completely empty (0 bytes or no rows).")
        except Exception as e:
            raise IngestionError(f"Failed to parse CSV file: {str(e)}")

        total_input_rows = len(df_raw)
        if total_input_rows == 0:
            raise IngestionError("The uploaded CSV contains 0 observation rows.")

        renamed_df, col_mapping = cls.normalize_column_names(df_raw)
        sensor = cls.detect_sensor(renamed_df, explicit_sensor)

        # Confirm minimal required coordinate fields exist
        missing_required_headers = []
        if "latitude" not in renamed_df.columns:
            missing_required_headers.append("latitude")
        if "longitude" not in renamed_df.columns:
            missing_required_headers.append("longitude")
        if "acq_date" not in renamed_df.columns and "date" not in renamed_df.columns:
            missing_required_headers.append("acq_date")

        if missing_required_headers:
            raise IngestionError(
                f"CSV lacks required geospatial columns: {', '.join(missing_required_headers)}. "
                "Active fire files must include latitude, longitude, and acquisition date."
            )

        # Default product metadata based on detected sensor
        if not product_name:
            if sensor == SensorType.MODIS:
                product_name = "MOD14_Terra_Collection_6_1"
            else:
                product_name = "VNP14IMGTDL_NPP_Collection_1"

        if not product_version:
            product_version = "C6.1" if sensor == SensorType.MODIS else "v1.0"

        # Row-level validation counters & flags
        valid_count = 0
        warning_count = 0
        rejected_count = 0
        duplicate_count = 0
        missing_coord_count = 0
        out_of_range_coord_count = 0
        malformed_time_count = 0
        missing_required_count = 0

        rejection_reasons: Dict[str, int] = {}
        warnings_list: List[str] = []

        def add_rejection(reason: str):
            nonlocal rejected_count
            rejected_count += 1
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

        row_statuses: List[RowQualityStatus] = []
        row_notes: List[List[str]] = []
        parsed_datetimes: List[Optional[datetime]] = []

        # Track seen coordinates + timestamps for duplicate detection
        seen_keys = set()

        for idx, row in renamed_df.iterrows():
            current_status = RowQualityStatus.VALID
            notes: List[str] = []

            # 1. Coordinate checks
            lat_raw = row.get("latitude")
            lon_raw = row.get("longitude")

            if pd.isna(lat_raw) or pd.isna(lon_raw):
                missing_coord_count += 1
                add_rejection("Missing latitude or longitude coordinate")
                row_statuses.append(RowQualityStatus.REJECTED)
                row_notes.append(["Missing coordinate values"])
                parsed_datetimes.append(None)
                continue

            try:
                lat = float(lat_raw)
                lon = float(lon_raw)
            except (ValueError, TypeError):
                missing_coord_count += 1
                add_rejection("Unparseable coordinate float")
                row_statuses.append(RowQualityStatus.REJECTED)
                row_notes.append(["Unparseable coordinate value"])
                parsed_datetimes.append(None)
                continue

            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                out_of_range_coord_count += 1
                add_rejection(f"Coordinates out of bounds: lat={lat}, lon={lon}")
                row_statuses.append(RowQualityStatus.REJECTED)
                row_notes.append([f"Coordinates out of bounds: lat={lat}, lon={lon}"])
                parsed_datetimes.append(None)
                continue

            # 2. Timestamp check
            date_raw = row.get("acq_date")
            time_raw = row.get("acq_time")
            dt_utc = cls.parse_datetime(date_raw, time_raw)

            if dt_utc is None:
                malformed_time_count += 1
                add_rejection(f"Malformed acquisition date or time: date={date_raw}, time={time_raw}")
                row_statuses.append(RowQualityStatus.REJECTED)
                row_notes.append(["Malformed acquisition timestamp"])
                parsed_datetimes.append(None)
                continue

            parsed_datetimes.append(dt_utc)

            # 3. Duplicate check (colocated point with exact same timestamp)
            row_key = (round(lat, 5), round(lon, 5), dt_utc.isoformat())
            if row_key in seen_keys:
                duplicate_count += 1
                add_rejection("Exact duplicate observation detected (colocated coordinates and identical timestamp)")
                row_statuses.append(RowQualityStatus.REJECTED)
                row_notes.append(["Exact duplicate observation"])
                continue
            seen_keys.add(row_key)

            # 4. Sensor-specific metadata & warning checks
            conf_raw = row.get("confidence")
            if sensor == SensorType.MODIS:
                if pd.notna(conf_raw):
                    try:
                        conf_val = float(conf_raw)
                        if conf_val < 30.0:
                            current_status = RowQualityStatus.WARNING
                            notes.append(f"Low confidence detection ({conf_val}%)")
                    except (ValueError, TypeError):
                        pass
            elif sensor == SensorType.VIIRS:
                if pd.notna(conf_raw):
                    conf_str = str(conf_raw).strip().lower()
                    if conf_str in ["l", "low"]:
                        current_status = RowQualityStatus.WARNING
                        notes.append("Low confidence detection (VIIRS flag 'low')")

            # Check scan / track swath edge
            track_val = row.get("track")
            if pd.notna(track_val):
                try:
                    if float(track_val) > 4.0:
                        current_status = RowQualityStatus.WARNING
                        notes.append(f"Near swath edge (track pixel size = {track_val}km)")
                except (ValueError, TypeError):
                    pass

            if current_status == RowQualityStatus.VALID:
                valid_count += 1
            else:
                warning_count += 1

            row_statuses.append(current_status)
            row_notes.append(notes)

        # Collect warning summary messages
        if warning_count > 0:
            warnings_list.append(
                f"{warning_count} observations flagged with scientific warnings (e.g., low confidence or edge pixels)."
            )
        if duplicate_count > 0:
            warnings_list.append(
                f"{duplicate_count} exact duplicate rows identified and excluded from valid analysis."
            )

        # Build schema mapping preview
        schema_mapping_preview: List[SchemaMappingPreviewItem] = []
        preview_fields = [
            ("latitude", "latitude", "degrees [-90, 90]"),
            ("longitude", "longitude", "degrees [-180, 180]"),
            ("acq_date", "observation_time_utc", "UTC ISO 8601"),
            ("confidence", "confidence_raw", "Sensor native scale"),
            ("frp", "frp_raw", "MW (Native units preserved)"),
        ]

        sample_row = renamed_df.iloc[0] if len(renamed_df) > 0 else {}
        for src_col, int_field, note in preview_fields:
            if src_col in renamed_df.columns:
                raw_sample = str(sample_row.get(src_col, ""))
                norm_sample = raw_sample
                if int_field == "observation_time_utc" and parsed_datetimes and parsed_datetimes[0]:
                    norm_sample = parsed_datetimes[0].isoformat()
                schema_mapping_preview.append(
                    SchemaMappingPreviewItem(
                        source_column=str(col_mapping.get(src_col, src_col)),
                        internal_field=int_field,
                        sample_raw_value=raw_sample,
                        sample_normalized_value=norm_sample,
                        unit_or_note=note,
                    )
                )

        # Compute spatio-temporal bounding box on valid records
        valid_indices = [i for i, st in enumerate(row_statuses) if st != RowQualityStatus.REJECTED]
        if valid_indices:
            valid_lats = [renamed_df.iloc[i]["latitude"] for i in valid_indices]
            valid_lons = [renamed_df.iloc[i]["longitude"] for i in valid_indices]
            valid_times = [parsed_datetimes[i] for i in valid_indices if parsed_datetimes[i] is not None]

            min_lon = float(min(valid_lons))
            max_lon = float(max(valid_lons))
            min_lat = float(min(valid_lats))
            max_lat = float(max(valid_lats))
            bbox = [min_lon, min_lat, max_lon, max_lat]

            min_time_utc = min(valid_times).isoformat() if valid_times else None
            max_time_utc = max(valid_times).isoformat() if valid_times else None
        else:
            bbox = None
            min_time_utc = None
            max_time_utc = None

        # Build validation report
        validation_report = ValidationReport(
            dataset_id=dataset_uuid,
            sensor=sensor,
            product_name=product_name,
            product_version=product_version,
            total_input_rows=total_input_rows,
            valid_count=valid_count,
            warning_count=warning_count,
            rejected_count=rejected_count,
            duplicate_row_count=duplicate_count,
            missing_coordinate_count=missing_coord_count,
            out_of_range_coordinate_count=out_of_range_coord_count,
            malformed_timestamp_count=malformed_time_count,
            missing_required_field_count=missing_required_count,
            rejection_reasons=rejection_reasons,
            warnings=warnings_list,
            schema_mapping_preview=schema_mapping_preview,
        )

        # Build dataset record
        now_iso = datetime.now(timezone.utc).isoformat()
        dataset_record = DatasetRecord(
            id=dataset_uuid,
            sensor=sensor,
            product_name=product_name,
            product_version=product_version,
            source_uri=source_uri,
            retrieved_at=now_iso,
            checksum=checksum,
            total_rows=total_input_rows,
            valid_rows=valid_count,
            warning_rows=warning_count,
            rejected_rows=rejected_count,
            min_time_utc=min_time_utc,
            max_time_utc=max_time_utc,
            bbox=bbox,
            metadata_json={
                "source_columns": list(df_raw.columns),
                "rejection_reasons": rejection_reasons,
                "warnings": warnings_list,
            },
            is_test_fixture=is_test_fixture,
        )

        # Attach audit columns to DataFrame
        renamed_df["_row_quality_status"] = [s.value for s in row_statuses]
        renamed_df["_quality_notes"] = row_notes
        renamed_df["_parsed_datetime"] = parsed_datetimes

        return validation_report, dataset_record, renamed_df
