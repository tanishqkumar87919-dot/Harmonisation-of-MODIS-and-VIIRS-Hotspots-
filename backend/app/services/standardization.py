"""Standardization service mapping MODIS and VIIRS records to the 17 internal fields."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from backend.app.schemas.common import RowQualityStatus, SensorType
from backend.app.schemas.dataset import DatasetRecord
from backend.app.schemas.observation import StandardizedObservation


class StandardizationService:
    """
    Transforms validated raw observation records into the authoritative internal schema.
    Strictly follows:
    - docs/04_DATA_SOURCES_AND_DICTIONARY.md (Section 4)
    - docs/05_HARMONISATION_ALGORITHM.md (Stage B)
    - Preserves native sensor physics, raw values, and full provenance back to source rows.
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
        "J1": "NOAA-20 (JPSS-1)",
        "NOAA-20": "NOAA-20 (JPSS-1)",
        "J2": "NOAA-21 (JPSS-2)",
        "NOAA-21": "NOAA-21 (JPSS-2)",
    }

    @classmethod
    def resolve_platform(cls, raw_val: Any, sensor: SensorType) -> str:
        """Resolve platform name cleanly from sensor/satellite metadata."""
        if pd.isna(raw_val) or raw_val is None:
            return "Terra" if sensor == SensorType.MODIS else "Suomi-NPP"

        cleaned = str(raw_val).strip().upper()
        if cleaned in cls.PLATFORM_NAME_MAP:
            return cls.PLATFORM_NAME_MAP[cleaned]
        for key, val in cls.PLATFORM_NAME_MAP.items():
            if key in cleaned:
                return val
        return str(raw_val).strip()

    @classmethod
    def standardize_records(
        cls,
        df: pd.DataFrame,
        dataset: DatasetRecord,
        ingestion_run_id: Optional[str] = None,
    ) -> List[StandardizedObservation]:
        """
        Convert validated DataFrame into a list of StandardizedObservation models.
        Traceable to source rows with all 17 internal fields preserved.
        """
        run_id = ingestion_run_id or f"ingest-{uuid.uuid4().hex[:8]}"
        standardized_list: List[StandardizedObservation] = []

        for idx, row in df.iterrows():
            row_dict = row.to_dict()

            # Retrieve audit metadata if populated by IngestionService
            status_val = row_dict.get("_row_quality_status", RowQualityStatus.VALID.value)
            try:
                row_status = RowQualityStatus(status_val)
            except ValueError:
                row_status = RowQualityStatus.VALID

            quality_notes = row_dict.get("_quality_notes", [])
            if not isinstance(quality_notes, list):
                quality_notes = []

            # 1. Observation & Source IDs
            obs_id = f"obs-{dataset.sensor.value.lower()}-{uuid.uuid4().hex[:10]}"
            source_rec_id = str(row_dict.get("id", row_dict.get("source_id", f"row-{idx}")))

            # 2. Platform & Sensor
            platform = cls.resolve_platform(row_dict.get("satellite"), dataset.sensor)

            # 3. Observation Time UTC
            parsed_dt = row_dict.get("_parsed_datetime")
            if isinstance(parsed_dt, datetime):
                obs_time_utc = parsed_dt.isoformat()
            else:
                date_val = row_dict.get("acq_date", "")
                time_val = row_dict.get("acq_time", "")
                obs_time_utc = f"{date_val}T{time_val}"

            # 4. Coordinates
            try:
                lat = float(row_dict.get("latitude", 0.0))
                lon = float(row_dict.get("longitude", 0.0))
            except (ValueError, TypeError):
                lat, lon = 0.0, 0.0

            # 5. Native Confidence (Preserved on original sensor scale)
            conf_raw = row_dict.get("confidence")
            if pd.isna(conf_raw) or conf_raw is None:
                cleaned_conf: Optional[Any] = None
            else:
                if dataset.sensor == SensorType.MODIS:
                    try:
                        cleaned_conf = float(conf_raw)
                    except (ValueError, TypeError):
                        cleaned_conf = str(conf_raw)
                else:
                    # VIIRS: usually string flag (e.g. nominal, high, low)
                    cleaned_conf = str(conf_raw).strip()

            # 6. FRP (MW) - Preserve without averaging or cross-sensor conversion
            frp_raw = row_dict.get("frp")
            cleaned_frp: Optional[float] = None
            if pd.notna(frp_raw):
                try:
                    cleaned_frp = float(frp_raw)
                except (ValueError, TypeError):
                    cleaned_frp = None

            # 7. Scan & Track pixel footprint
            scan_raw = row_dict.get("scan")
            cleaned_scan = float(scan_raw) if pd.notna(scan_raw) and str(scan_raw).replace(".", "", 1).isdigit() else None

            track_raw = row_dict.get("track")
            cleaned_track = float(track_raw) if pd.notna(track_raw) and str(track_raw).replace(".", "", 1).isdigit() else None

            # 8. Sensor Quality Flags and Brightness channels
            quality_flags: Dict[str, Any] = {}
            if "daynight" in row_dict and pd.notna(row_dict["daynight"]):
                quality_flags["daynight"] = str(row_dict["daynight"]).strip()
            if "brightness" in row_dict and pd.notna(row_dict["brightness"]):
                quality_flags["brightness"] = row_dict["brightness"]
            if "bright_t31" in row_dict and pd.notna(row_dict["bright_t31"]):
                quality_flags["bright_t31"] = row_dict["bright_t31"]
            if "bright_ti4" in row_dict and pd.notna(row_dict["bright_ti4"]):
                quality_flags["bright_ti4"] = row_dict["bright_ti4"]
            if "bright_ti5" in row_dict and pd.notna(row_dict["bright_ti5"]):
                quality_flags["bright_ti5"] = row_dict["bright_ti5"]

            # Filter internal private fields from raw_fields copy
            public_raw_fields = {
                k: v for k, v in row_dict.items() if not str(k).startswith("_") and pd.notna(v)
            }

            observation = StandardizedObservation(
                observation_id=obs_id,
                dataset_id=dataset.id,
                source_record_id=source_rec_id,
                source_sensor=dataset.sensor,
                platform=platform,
                product_name=dataset.product_name,
                product_version=dataset.product_version,
                observation_time_utc=obs_time_utc,
                latitude=lat,
                longitude=lon,
                confidence_raw=cleaned_conf,
                frp_raw=cleaned_frp,
                frp_unit="MW" if cleaned_frp is not None else None,
                scan_raw=cleaned_scan,
                track_raw=cleaned_track,
                quality_flags_raw=quality_flags,
                ingestion_run_id=run_id,
                row_quality_status=row_status,
                quality_notes=quality_notes,
                raw_fields=public_raw_fields,
            )

            standardized_list.append(observation)

        return standardized_list

    @classmethod
    def get_eligible_observations(
        cls,
        observations: List[StandardizedObservation],
        include_warnings: bool = True,
        min_modis_confidence: Optional[float] = None,
        allowed_viirs_confidence_levels: Optional[List[str]] = None,
    ) -> List[StandardizedObservation]:
        """
        Filter standardized observations for harmonisation matching eligibility
        according to configured scientific quality rules.
        """
        eligible = []
        for obs in observations:
            # Exclude rejected rows always
            if obs.row_quality_status == RowQualityStatus.REJECTED:
                continue

            # Warning filtering
            if obs.row_quality_status == RowQualityStatus.WARNING and not include_warnings:
                continue

            # MODIS confidence threshold check
            if obs.source_sensor == SensorType.MODIS and min_modis_confidence is not None:
                if obs.confidence_raw is not None:
                    try:
                        conf_val = float(obs.confidence_raw)
                        if conf_val < min_modis_confidence:
                            continue
                    except (ValueError, TypeError):
                        pass

            # VIIRS allowed confidence levels check
            if obs.source_sensor == SensorType.VIIRS and allowed_viirs_confidence_levels:
                if obs.confidence_raw is not None:
                    conf_str = str(obs.confidence_raw).strip().lower()
                    allowed_lower = [str(x).strip().lower() for x in allowed_viirs_confidence_levels]
                    if conf_str not in allowed_lower:
                        continue

            eligible.append(obs)

        return eligible
