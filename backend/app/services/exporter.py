"""Reproducible CSV and GeoJSON Exporter adhering to FR-19 and docs/05_HARMONISATION_ALGORITHM.md."""

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.schemas.common import MatchStatus, SensorType
from backend.app.schemas.matching import HarmonisedRecord
from backend.app.schemas.runs import ProcessingRunSummary


class ExporterService:
    """
    Exports harmonised observations to CSV and GeoJSON formats:
    - Retains full source provenance and sensor parameters.
    - Preserves separate sensor FRP fields and units without cross-sensor averaging.
    - Embeds reproducibility metadata (run_id, thresholds, method_version, timestamp).
    """

    SCIENTIFIC_LIMITATIONS_NOTE = (
        "MODIS and VIIRS active-fire hotspot detections harmonised under documented "
        "spatial and temporal thresholds. Native sensor footprints (1km vs 375m) and point-spread "
        "functions differ. FRP values represent sensor-specific radiative energy and must not be averaged."
    )

    @classmethod
    def filter_records(
        cls,
        records: List[HarmonisedRecord],
        match_status: Optional[str] = None,
        sensor: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> Tuple[List[HarmonisedRecord], Dict[str, Any]]:
        """Filter records by match_status, sensor, temporal window, and spatial bounding box."""
        filtered = list(records)
        filters_applied: Dict[str, Any] = {}

        # 1. Match Status filter
        if match_status:
            statuses = [s.strip().lower() for s in match_status.split(",") if s.strip()]
            filtered = [r for r in filtered if r.match_status.value.lower() in statuses]
            filters_applied["match_status"] = statuses

        # 2. Sensor filter
        if sensor:
            sens_clean = sensor.strip().upper()
            if "MODIS" in sens_clean and "VIIRS" not in sens_clean:
                filtered = [
                    r for r in filtered
                    if r.match_status in [MatchStatus.MATCHED, MatchStatus.AMBIGUOUS, MatchStatus.UNMATCHED_MODIS]
                ]
            elif "VIIRS" in sens_clean and "MODIS" not in sens_clean:
                filtered = [
                    r for r in filtered
                    if r.match_status in [MatchStatus.MATCHED, MatchStatus.AMBIGUOUS, MatchStatus.UNMATCHED_VIIRS]
                ]
            filters_applied["sensor"] = sens_clean

        # 3. Temporal window filter
        if start_time or end_time:
            time_filtered = []
            for r in filtered:
                t_str = (
                    r.modis_observation.observation_time_utc if r.modis_observation
                    else (r.viirs_observation.observation_time_utc if r.viirs_observation else None)
                )
                if not t_str:
                    time_filtered.append(r)
                    continue
                if start_time and t_str < start_time:
                    continue
                if end_time and t_str > end_time:
                    continue
                time_filtered.append(r)
            filtered = time_filtered
            filters_applied["start_time"] = start_time
            filters_applied["end_time"] = end_time

        # 4. Bounding box filter: [min_lon, min_lat, max_lon, max_lat]
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            bbox_filtered = []
            for r in filtered:
                lat = (
                    r.viirs_observation.latitude if r.viirs_observation
                    else (r.modis_observation.latitude if r.modis_observation else None)
                )
                lon = (
                    r.viirs_observation.longitude if r.viirs_observation
                    else (r.modis_observation.longitude if r.modis_observation else None)
                )
                if lat is None or lon is None:
                    continue
                if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                    bbox_filtered.append(r)
            filtered = bbox_filtered
            filters_applied["bbox"] = list(bbox)

        return filtered, filters_applied

    @classmethod
    def export_to_csv(
        cls,
        run: ProcessingRunSummary,
        records: List[HarmonisedRecord],
        filters_applied: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export harmonised records to reproducible CSV string."""
        now_utc = datetime.now(timezone.utc).isoformat()
        filter_str = json.dumps(filters_applied or {})

        output = io.StringIO()
        fieldnames = [
            "harmonisation_id",
            "run_id",
            "match_status",
            "modis_observation_id",
            "viirs_observation_id",
            "modis_source_record_id",
            "viirs_source_record_id",
            "modis_product_version",
            "viirs_product_version",
            "modis_time_utc",
            "viirs_time_utc",
            "modis_lat",
            "modis_lon",
            "viirs_lat",
            "viirs_lon",
            "spatial_distance_m",
            "time_difference_s",
            "match_score",
            "modis_confidence_raw",
            "viirs_confidence_raw",
            "modis_frp_raw",
            "viirs_frp_raw",
            "frp_unit",
            "matching_method_version",
            "max_distance_meters",
            "max_time_difference_seconds",
            "ambiguity_policy",
            "exported_at_utc",
            "filter_applied",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for r in records:
            m = r.modis_observation
            v = r.viirs_observation
            writer.writerow({
                "harmonisation_id": r.harmonisation_id,
                "run_id": r.run_id,
                "match_status": r.match_status.value,
                "modis_observation_id": r.modis_observation_id or "",
                "viirs_observation_id": r.viirs_observation_id or "",
                "modis_source_record_id": r.provenance.modis_source_record_id or "",
                "viirs_source_record_id": r.provenance.viirs_source_record_id or "",
                "modis_product_version": r.provenance.modis_product_version or "",
                "viirs_product_version": r.provenance.viirs_product_version or "",
                "modis_time_utc": m.observation_time_utc if m else "",
                "viirs_time_utc": v.observation_time_utc if v else "",
                "modis_lat": m.latitude if m else "",
                "modis_lon": m.longitude if m else "",
                "viirs_lat": v.latitude if v else "",
                "viirs_lon": v.longitude if v else "",
                "spatial_distance_m": r.spatial_distance_m if r.spatial_distance_m is not None else "",
                "time_difference_s": r.time_difference_s if r.time_difference_s is not None else "",
                "match_score": r.match_score if r.match_score is not None else "",
                "modis_confidence_raw": m.confidence_raw if m and m.confidence_raw is not None else "",
                "viirs_confidence_raw": v.confidence_raw if v and v.confidence_raw is not None else "",
                "modis_frp_raw": m.frp_raw if m and m.frp_raw is not None else "",
                "viirs_frp_raw": v.frp_raw if v and v.frp_raw is not None else "",
                "frp_unit": "MW",
                "matching_method_version": r.matching_method_version,
                "max_distance_meters": run.parameters.max_distance_meters,
                "max_time_difference_seconds": run.parameters.max_time_difference_seconds,
                "ambiguity_policy": run.parameters.ambiguity_policy.value,
                "exported_at_utc": now_utc,
                "filter_applied": filter_str,
            })

        return output.getvalue()

    @classmethod
    def export_to_geojson(
        cls,
        run: ProcessingRunSummary,
        records: List[HarmonisedRecord],
        filters_applied: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Export harmonised records to GeoJSON FeatureCollection dictionary."""
        now_utc = datetime.now(timezone.utc).isoformat()

        features: List[Dict[str, Any]] = []
        for r in records:
            m = r.modis_observation
            v = r.viirs_observation

            # Geometry: VIIRS coordinate preferred (finer resolution), else MODIS
            if v and v.latitude != 0.0 and v.longitude != 0.0:
                coord = [v.longitude, v.latitude]
            elif m and m.latitude != 0.0 and m.longitude != 0.0:
                coord = [m.longitude, m.latitude]
            else:
                coord = [0.0, 0.0]

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": coord,
                },
                "properties": {
                    "harmonisation_id": r.harmonisation_id,
                    "run_id": r.run_id,
                    "match_status": r.match_status.value,
                    "spatial_distance_m": r.spatial_distance_m,
                    "time_difference_s": r.time_difference_s,
                    "match_score": r.match_score,
                    "modis_observation_id": r.modis_observation_id,
                    "viirs_observation_id": r.viirs_observation_id,
                    "modis_source_record_id": r.provenance.modis_source_record_id,
                    "viirs_source_record_id": r.provenance.viirs_source_record_id,
                    "modis_confidence": m.confidence_raw if m else None,
                    "viirs_confidence": v.confidence_raw if v else None,
                    "modis_frp_mw": m.frp_raw if m else None,
                    "viirs_frp_mw": v.frp_raw if v else None,
                    "modis_time_utc": m.observation_time_utc if m else None,
                    "viirs_time_utc": v.observation_time_utc if v else None,
                    "candidate_count": r.provenance.candidate_count,
                    "decision_reason": r.provenance.decision_reason,
                },
            }
            features.append(feature)

        geojson_doc = {
            "type": "FeatureCollection",
            "metadata": {
                "run_id": run.run_id,
                "method_version": run.method_version,
                "matching_parameters": run.parameters.model_dump(),
                "filter_applied": filters_applied or {},
                "exported_at_utc": now_utc,
                "total_features": len(features),
                "scientific_limitations_note": cls.SCIENTIFIC_LIMITATIONS_NOTE,
            },
            "features": features,
        }

        return geojson_doc
