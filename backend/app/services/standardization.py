"""Stages B & C: Standardization, Quality Control, and Schema Mapping Service."""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from backend.app.schemas.datasets import (
    DatasetRecordSchema,
    DatasetValidationReportSchema,
    RowQualityStatus,
    SchemaMappingPreviewItem,
    SensorType,
)
from backend.app.schemas.observations import StandardizedObservationSchema


class StandardizationService:
    """
    Stage B: Standardization to 17 internal fields.
    Stage C: Rigorous row-level Quality Control (valid, warning, rejected).
    """

    PLATFORM_NAME_MAP = {
        "T": "Terra",
        "TERRA": "Terra",
        "A": "Aqua",
        "AQUA": "Aqua",
        "N": "Suomi-NPP",
        "SNPP": "Suomi-NPP",
        "SUOMI-NPP": "Suomi-NPP",
        "NPP": "Suomi-NPP",
        "J1": "NOAA-20",
        "N20": "NOAA-20",
        "NOAA-20": "NOAA-20",
        "NOAA20": "NOAA-20",
        "J2": "NOAA-21",
        "N21": "NOAA-21",
        "NOAA-21": "NOAA-21",
    }

    SENTINEL_FRP_VALUES = {-999.0, -9999.0, 9999.0, 9999.9}

    @classmethod
    def resolve_platform(cls, raw_val: Any, sensor: SensorType) -> str:
        """Map satellite abbreviation to standardized platform name."""
        if not raw_val or pd.isna(raw_val) or str(raw_val).strip() == "":
            return "Terra" if sensor == SensorType.MODIS else "Suomi-NPP"

        cleaned = str(raw_val).strip().upper()
        if cleaned in cls.PLATFORM_NAME_MAP:
            return cls.PLATFORM_NAME_MAP[cleaned]
        for key, val in cls.PLATFORM_NAME_MAP.items():
            if key in cleaned:
                return val
        return str(raw_val).strip()

    @classmethod
    def parse_timestamp_utc(
        cls, date_str: Optional[str], time_str: Optional[str] = None
    ) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Parse date and time into timezone-aware UTC datetime.
        Returns (parsed_datetime, error_reason).
        """
        if not date_str or str(date_str).strip() == "":
            return None, "malformed_or_missing_timestamp"

        clean_date = str(date_str).strip()

        # Handle full ISO-8601 string
        if "T" in clean_date or (" " in clean_date and len(clean_date) > 10):
            try:
                # pandas to_datetime handles various ISO formats
                dt = pd.to_datetime(clean_date, utc=True)
                if pd.isna(dt):
                    return None, "malformed_or_missing_timestamp"
                return dt.to_pydatetime(), None
            except Exception:
                return None, "malformed_or_missing_timestamp"

        # Validate date format (YYYY-MM-DD or YYYY/MM/DD)
        date_pattern = r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$"
        match = re.match(date_pattern, clean_date)
        if not match:
            return None, "malformed_or_missing_timestamp"

        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if not (1 <= month <= 12 and 1 <= day <= 31):
            return None, "malformed_or_missing_timestamp"

        # Parse acq_time
        hour, minute, second = 0, 0, 0
        if time_str is not None and str(time_str).strip() != "":
            raw_t = str(time_str).strip()
            if raw_t.endswith(".0"):
                raw_t = raw_t[:-2]

            if ":" in raw_t:
                parts = raw_t.split(":")
                try:
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    second = int(float(parts[2])) if len(parts) > 2 else 0
                except (ValueError, TypeError):
                    return None, "malformed_or_missing_timestamp"
            else:
                if not raw_t.isdigit():
                    return None, "malformed_or_missing_timestamp"
                padded = raw_t.zfill(4)
                try:
                    hour = int(padded[:2])
                    minute = int(padded[2:4])
                    second = int(padded[4:6]) if len(padded) >= 6 else 0
                except (ValueError, TypeError):
                    return None, "malformed_or_missing_timestamp"

        # Strict 24h validation
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            return None, "malformed_or_missing_timestamp"

        try:
            dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            return dt, None
        except ValueError:
            return None, "malformed_or_missing_timestamp"

    @classmethod
    def process_and_standardize(
        cls,
        df_raw: pd.DataFrame,
        dataset_id: str,
        sensor: SensorType,
        product_name: str,
        product_version: str,
        source_uri: str,
        checksum: str,
        ingestion_run_id: str,
        is_test_fixture: bool = False,
    ) -> Tuple[DatasetValidationReportSchema, DatasetRecordSchema, List[StandardizedObservationSchema]]:
        """
        Execute Stages B & C:
        Transform input DataFrame into validated StandardizedObservationSchemas,
        compute quality counters, and produce the ValidationReport and DatasetRecord.
        """
        total_input_rows = len(df_raw)
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

        def record_rejection(reason: str):
            nonlocal rejected_count
            rejected_count += 1
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

        observations: List[StandardizedObservationSchema] = []
        seen_keys = set()

        for idx, row in df_raw.iterrows():
            row_dict = {str(k): ("" if pd.isna(v) else str(v).strip()) for k, v in row.items()}
            quality_status = RowQualityStatus.VALID
            quality_notes: List[str] = []

            # Determine source record ID
            source_rec_id = (
                row_dict.get("id")
                or row_dict.get("source_record_id")
                or row_dict.get("fire_id")
                or f"{sensor.value.lower()}_{product_name}_{idx}"
            )

            # Platform
            platform = cls.resolve_platform(row_dict.get("satellite"), sensor)

            # 1. Coordinate Validation
            lat_str = row_dict.get("latitude")
            lon_str = row_dict.get("longitude")
            lat_float: Optional[float] = None
            lon_float: Optional[float] = None

            if not lat_str or not lon_str:
                missing_coord_count += 1
                record_rejection("invalid_or_out_of_range_latitude" if not lat_str else "invalid_or_out_of_range_longitude")
                quality_status = RowQualityStatus.REJECTED
                quality_notes.append("missing_coordinates")
            else:
                try:
                    lat_float = float(lat_str)
                    lon_float = float(lon_str)
                    if not (-90.0 <= lat_float <= 90.0):
                        out_of_range_coord_count += 1
                        record_rejection("invalid_or_out_of_range_latitude")
                        quality_status = RowQualityStatus.REJECTED
                        quality_notes.append("invalid_or_out_of_range_latitude")
                    elif not (-180.0 <= lon_float <= 180.0):
                        out_of_range_coord_count += 1
                        record_rejection("invalid_or_out_of_range_longitude")
                        quality_status = RowQualityStatus.REJECTED
                        quality_notes.append("invalid_or_out_of_range_longitude")
                except ValueError:
                    missing_coord_count += 1
                    record_rejection("invalid_or_out_of_range_latitude")
                    quality_status = RowQualityStatus.REJECTED
                    quality_notes.append("unparseable_coordinate_float")

            # 2. Timestamp Validation
            date_field = row_dict.get("acq_date") or row_dict.get("observation_time_utc")
            time_field = row_dict.get("acq_time")
            parsed_dt, time_err = cls.parse_timestamp_utc(date_field, time_field)

            if parsed_dt is None:
                malformed_time_count += 1
                record_rejection("malformed_or_missing_timestamp")
                quality_status = RowQualityStatus.REJECTED
                quality_notes.append("malformed_or_missing_timestamp")
                obs_time_iso = str(date_field or "")
            else:
                obs_time_iso = parsed_dt.isoformat()

            # 3. Duplicate Detection
            if quality_status != RowQualityStatus.REJECTED and lat_float is not None and lon_float is not None and parsed_dt:
                row_key = (round(lat_float, 5), round(lon_float, 5), obs_time_iso)
                if row_key in seen_keys:
                    duplicate_count += 1
                    record_rejection("duplicate_source_row")
                    quality_status = RowQualityStatus.REJECTED
                    quality_notes.append("duplicate_source_row")
                else:
                    seen_keys.add(row_key)

            # 4. Stage C Warning Rules (for non-rejected rows)
            # FRP check
            frp_raw_str = row_dict.get("frp")
            frp_float: Optional[float] = None
            if not frp_raw_str:
                if quality_status != RowQualityStatus.REJECTED:
                    quality_status = RowQualityStatus.WARNING
                    quality_notes.append("missing_or_negative_frp")
            else:
                try:
                    frp_val = float(frp_raw_str)
                    if frp_val in cls.SENTINEL_FRP_VALUES or frp_val < 0.0:
                        if quality_status != RowQualityStatus.REJECTED:
                            quality_status = RowQualityStatus.WARNING
                            quality_notes.append("missing_or_negative_frp")
                    else:
                        frp_float = frp_val
                except ValueError:
                    if quality_status != RowQualityStatus.REJECTED:
                        quality_status = RowQualityStatus.WARNING
                        quality_notes.append("missing_or_negative_frp")

            # Confidence check
            conf_raw_str = row_dict.get("confidence")
            cleaned_conf: Optional[Union[str, int, float]] = None
            if not conf_raw_str:
                if quality_status != RowQualityStatus.REJECTED:
                    quality_status = RowQualityStatus.WARNING
                    quality_notes.append("missing_confidence")
            else:
                cleaned_conf = conf_raw_str
                if sensor == SensorType.VIIRS and str(conf_raw_str).strip().lower() in ["l", "low"]:
                    if quality_status != RowQualityStatus.REJECTED:
                        quality_status = RowQualityStatus.WARNING
                        quality_notes.append("low_confidence_detection")
                elif sensor == SensorType.MODIS:
                    try:
                        if float(conf_raw_str) < 30.0 and quality_status != RowQualityStatus.REJECTED:
                            quality_status = RowQualityStatus.WARNING
                            quality_notes.append("low_confidence_detection")
                    except ValueError:
                        pass

            # Scan and track footprint check
            scan_str = row_dict.get("scan")
            track_str = row_dict.get("track")
            scan_float: Optional[float] = None
            track_float: Optional[float] = None
            if not scan_str or not track_str:
                if quality_status != RowQualityStatus.REJECTED:
                    quality_status = RowQualityStatus.WARNING
                    quality_notes.append("missing_scan_track_footprint")
            else:
                try:
                    scan_float = float(scan_str)
                    track_float = float(track_str)
                except ValueError:
                    if quality_status != RowQualityStatus.REJECTED:
                        quality_status = RowQualityStatus.WARNING
                        quality_notes.append("missing_scan_track_footprint")

            # Quality flags
            quality_flags: Dict[str, Any] = {}
            for qf in ["daynight", "type", "brightness", "bright_t31", "bright_ti4", "bright_ti5"]:
                if qf in row_dict and row_dict[qf] != "":
                    quality_flags[qf] = row_dict[qf]

            # Update summary counts
            if quality_status == RowQualityStatus.VALID:
                valid_count += 1
            elif quality_status == RowQualityStatus.WARNING:
                warning_count += 1

            # Construct StandardizedObservationSchema (Retaining rejected rows per requirements)
            obs = StandardizedObservationSchema(
                observation_id=f"obs-{sensor.value.lower()}-{uuid.uuid4().hex[:10]}",
                dataset_id=dataset_id,
                source_record_id=source_rec_id,
                source_sensor=sensor,
                platform=platform,
                product_name=product_name,
                product_version=product_version,
                observation_time_utc=obs_time_iso,
                latitude=lat_float if lat_float is not None and -90.0 <= lat_float <= 90.0 else 0.0,
                longitude=lon_float if lon_float is not None and -180.0 <= lon_float <= 180.0 else 0.0,
                confidence_raw=cleaned_conf,
                frp_raw=frp_float,
                frp_unit="MW" if frp_float is not None else None,
                scan_raw=scan_float,
                track_raw=track_float,
                quality_flags_raw=quality_flags,
                ingestion_run_id=ingestion_run_id,
                row_quality_status=quality_status,
                quality_notes=quality_notes,
                raw_fields=row_dict,
            )
            observations.append(obs)

        # Generate warnings list
        if warning_count > 0:
            warnings_list.append(f"{warning_count} rows flagged with quality warnings (e.g. missing FRP or confidence).")
        if duplicate_count > 0:
            warnings_list.append(f"{duplicate_count} duplicate source rows detected and rejected.")

        # Compute bounding box and temporal bounds on valid and warning rows
        eligible_obs = [o for o in observations if o.row_quality_status != RowQualityStatus.REJECTED]
        if eligible_obs:
            lats = [o.latitude for o in eligible_obs]
            lons = [o.longitude for o in eligible_obs]
            bbox = [min(lons), min(lats), max(lons), max(lats)]
            times = [o.observation_time_utc for o in eligible_obs if o.observation_time_utc]
            min_time = min(times) if times else None
            max_time = max(times) if times else None
        else:
            bbox = None
            min_time = None
            max_time = None

        # Build schema mapping preview items
        schema_mapping_preview = [
            SchemaMappingPreviewItem(
                source_column="latitude",
                internal_field="latitude",
                sample_raw_value=str(observations[0].raw_fields.get("latitude", "") if observations else ""),
                sample_normalized_value=str(observations[0].latitude if observations else ""),
                unit_or_note="degrees [-90.0, 90.0]",
            ),
            SchemaMappingPreviewItem(
                source_column="longitude",
                internal_field="longitude",
                sample_raw_value=str(observations[0].raw_fields.get("longitude", "") if observations else ""),
                sample_normalized_value=str(observations[0].longitude if observations else ""),
                unit_or_note="degrees [-180.0, 180.0]",
            ),
            SchemaMappingPreviewItem(
                source_column="acq_date + acq_time",
                internal_field="observation_time_utc",
                sample_raw_value=f"{observations[0].raw_fields.get('acq_date', '')} {observations[0].raw_fields.get('acq_time', '')}" if observations else "",
                sample_normalized_value=observations[0].observation_time_utc if observations else "",
                unit_or_note="Timezone-aware UTC ISO-8601",
            ),
            SchemaMappingPreviewItem(
                source_column="confidence",
                internal_field="confidence_raw",
                sample_raw_value=str(observations[0].confidence_raw or "") if observations else "",
                sample_normalized_value=str(observations[0].confidence_raw or "") if observations else "",
                unit_or_note="Sensor-specific scale preserved",
            ),
            SchemaMappingPreviewItem(
                source_column="frp",
                internal_field="frp_raw",
                sample_raw_value=str(observations[0].raw_fields.get("frp", "") if observations else ""),
                sample_normalized_value=str(observations[0].frp_raw or "") if observations else "",
                unit_or_note="MW (Preserved without averaging)",
            ),
        ]

        report = DatasetValidationReportSchema(
            dataset_id=dataset_id,
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

        now_iso = datetime.now(timezone.utc).isoformat()
        dataset_record = DatasetRecordSchema(
            id=dataset_id,
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
            min_time_utc=min_time,
            max_time_utc=max_time,
            bbox=bbox,
            metadata_json={
                "rejection_reasons": rejection_reasons,
                "warnings": warnings_list,
            },
            is_test_fixture=is_test_fixture,
        )

        return report, dataset_record, observations

    @classmethod
    def standardize_records(
        cls,
        df: pd.DataFrame,
        dataset: DatasetRecordSchema,
        ingestion_run_id: Optional[str] = None,
    ) -> List[StandardizedObservationSchema]:
        """Backwards compatible helper returning observations list."""
        renamed_df, _ = IngestionService.normalize_column_names(df) if "latitude" not in df.columns else (df, {})
        from backend.app.services.ingestion import IngestionService
        _, _, observations = cls.process_and_standardize(
            df_raw=df,
            dataset_id=dataset.id,
            sensor=dataset.sensor,
            product_name=dataset.product_name,
            product_version=dataset.product_version,
            source_uri=dataset.source_uri,
            checksum=dataset.checksum,
            ingestion_run_id=ingestion_run_id or "ingest-legacy",
            is_test_fixture=dataset.is_test_fixture,
        )
        return observations

    @classmethod
    def get_eligible_observations(
        cls,
        observations: List[StandardizedObservationSchema],
        include_warnings: bool = True,
        min_modis_confidence: Optional[float] = None,
        allowed_viirs_confidence_levels: Optional[List[str]] = None,
    ) -> List[StandardizedObservationSchema]:
        """
        Filter observations eligible for Stage D matching.
        Strictly excludes rejected rows.
        """
        eligible = []
        for obs in observations:
            if obs.row_quality_status == RowQualityStatus.REJECTED:
                continue

            if obs.row_quality_status == RowQualityStatus.WARNING and not include_warnings:
                continue

            if obs.source_sensor == SensorType.MODIS and min_modis_confidence is not None:
                if obs.confidence_raw is not None:
                    try:
                        conf_val = float(obs.confidence_raw)
                        if conf_val < min_modis_confidence:
                            continue
                    except (ValueError, TypeError):
                        pass

            if obs.source_sensor == SensorType.VIIRS and allowed_viirs_confidence_levels:
                if obs.confidence_raw is not None:
                    conf_str = str(obs.confidence_raw).strip().lower()
                    allowed_lower = [str(x).strip().lower() for x in allowed_viirs_confidence_levels]
                    if conf_str not in allowed_lower:
                        continue

            eligible.append(obs)

        return eligible
