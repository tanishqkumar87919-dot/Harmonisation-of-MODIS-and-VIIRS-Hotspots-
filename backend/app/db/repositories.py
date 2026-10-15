"""Database repository layer providing typed CRUD, PostGIS spatial queries, and SQLite compatibility."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from backend.app.db.models import (
    DatasetModel,
    HarmonisedRecordModel,
    MatchCandidateModel,
    ObservationModel,
    ProcessingRunModel,
)
from backend.app.services.matching_engine import MatchingEngineService


def ensure_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    """Safely convert any identifier (standard UUID or prefixed string) to UUID."""
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        # Generate deterministic UUID5 for custom prefixed string IDs
        return uuid.uuid5(uuid.NAMESPACE_DNS, str(val))


class DatasetRepository:
    """Repository managing dataset records and their bulk raw observations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        dataset: Any,
        observations: List[Any],
        raw_bytes: bytes = b"",
    ) -> DatasetModel:
        """Persist a dataset and all child observations in a single transaction."""
        dataset_uid = ensure_uuid(getattr(dataset, "id", None) or uuid.uuid4())

        meta = getattr(dataset, "metadata_json", None) or {}
        if not isinstance(meta, dict):
            meta = meta.model_dump() if hasattr(meta, "model_dump") else dict(meta)

        # Store original string ID if custom format
        orig_id = str(getattr(dataset, "id", dataset_uid))
        meta["external_id"] = orig_id
        if raw_bytes:
            meta["raw_size_bytes"] = len(raw_bytes)

        retrieved_at = getattr(dataset, "retrieved_at", None)
        if isinstance(retrieved_at, str):
            retrieved_at = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        elif not isinstance(retrieved_at, datetime):
            retrieved_at = datetime.now(timezone.utc)

        sensor_val = getattr(dataset, "sensor", "MODIS")
        if hasattr(sensor_val, "value"):
            sensor_str = str(sensor_val.value)
        else:
            sensor_str = str(sensor_val).replace("SensorType.", "")

        dataset_model = DatasetModel(
            id=dataset_uid,
            sensor=sensor_str,
            product_name=str(getattr(dataset, "product_name", "Unknown")),
            product_version=str(getattr(dataset, "product_version", "1.0")),
            source_uri=getattr(dataset, "source_uri", None),
            retrieved_at=retrieved_at,
            checksum=getattr(dataset, "checksum", None),
            metadata_json=meta,
        )
        self.session.add(dataset_model)

        # Build ObservationModel rows
        obs_models: List[ObservationModel] = []
        for obs in observations:
            obs_uid = ensure_uuid(getattr(obs, "observation_id", None) or uuid.uuid4())
            obs_time = getattr(obs, "observation_time_utc", None)
            if isinstance(obs_time, str):
                try:
                    obs_time = datetime.fromisoformat(obs_time.replace("Z", "+00:00"))
                except ValueError:
                    obs_time = None

            obs_sensor_val = getattr(obs, "source_sensor", sensor_str)
            if hasattr(obs_sensor_val, "value"):
                obs_sensor = str(obs_sensor_val.value)
            else:
                obs_sensor = str(obs_sensor_val).replace("SensorType.", "")

            obs_status_val = getattr(obs, "row_quality_status", "valid")
            if hasattr(obs_status_val, "value"):
                obs_status = str(obs_status_val.value)
            else:
                obs_status = str(obs_status_val).replace("RowQualityStatus.", "")

            notes = getattr(obs, "quality_notes", None) or []
            if not isinstance(notes, list):
                notes = list(notes)

            raw = getattr(obs, "raw_fields", None) or {}
            if not isinstance(raw, dict):
                raw = raw.model_dump() if hasattr(raw, "model_dump") else dict(raw)

            obs_model = ObservationModel(
                id=obs_uid,
                dataset_id=dataset_uid,
                source_record_id=str(getattr(obs, "source_record_id", f"rec-{obs_uid.hex[:8]}")),
                sensor=str(obs_sensor),
                observed_at=obs_time,
                latitude=getattr(obs, "latitude", None),
                longitude=getattr(obs, "longitude", None),
                confidence_raw=str(getattr(obs, "confidence_raw", None)) if getattr(obs, "confidence_raw", None) is not None else None,
                frp_raw=float(getattr(obs, "frp_raw", 0.0)) if getattr(obs, "frp_raw", None) is not None else None,
                frp_unit=getattr(obs, "frp_unit", None),
                raw_fields=raw,
                quality_status=str(obs_status),
                quality_notes=notes,
            )
            obs_models.append(obs_model)

        self.session.add_all(obs_models)
        self.session.flush()
        return dataset_model

    def get(self, dataset_id: Union[str, uuid.UUID]) -> Optional[DatasetModel]:
        """Fetch dataset by UUID or string ID."""
        uid = ensure_uuid(dataset_id)
        # First try direct primary key lookup
        ds = self.session.get(DatasetModel, uid)
        if ds:
            return ds
        # Fallback to external_id inside metadata_json if string format differs
        stmt = select(DatasetModel).filter(
            DatasetModel.metadata_json["external_id"].as_string() == str(dataset_id)
        )
        return self.session.scalars(stmt).first()

    def list_all(self) -> List[DatasetModel]:
        """List all datasets ordered by retrieval date descending."""
        stmt = select(DatasetModel).order_by(DatasetModel.retrieved_at.desc())
        return list(self.session.scalars(stmt).all())

    def delete(self, dataset_id: Union[str, uuid.UUID]) -> bool:
        """Delete a dataset and cascade to child observations."""
        ds = self.get(dataset_id)
        if not ds:
            return False
        self.session.delete(ds)
        self.session.flush()
        return True


class ObservationRepository:
    """Repository querying observation records and applying quality filters."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, observation_id: Union[str, uuid.UUID]) -> Optional[ObservationModel]:
        return self.session.get(ObservationModel, ensure_uuid(observation_id))

    def get_by_dataset(
        self,
        dataset_id: Union[str, uuid.UUID],
        limit: int = 1000,
        offset: int = 0,
    ) -> List[ObservationModel]:
        uid = ensure_uuid(dataset_id)
        stmt = (
            select(ObservationModel)
            .filter(ObservationModel.dataset_id == uid)
            .order_by(ObservationModel.source_record_id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def count_by_dataset(self, dataset_id: Union[str, uuid.UUID]) -> int:
        uid = ensure_uuid(dataset_id)
        stmt = select(ObservationModel).filter(ObservationModel.dataset_id == uid)
        return len(list(self.session.scalars(stmt).all()))

    def get_eligible(
        self,
        dataset_id: Union[str, uuid.UUID],
        include_warnings: bool = False,
        min_modis_confidence: Optional[int] = None,
        allowed_viirs_confidence_levels: Optional[List[str]] = None,
    ) -> List[ObservationModel]:
        """Fetch observations meeting filtering and quality eligibility criteria."""
        uid = ensure_uuid(dataset_id)
        allowed_statuses = ["valid"]
        if include_warnings:
            allowed_statuses.append("warning")

        stmt = select(ObservationModel).filter(
            ObservationModel.dataset_id == uid,
            ObservationModel.quality_status.in_(allowed_statuses),
            ObservationModel.latitude.isnot(None),
            ObservationModel.longitude.isnot(None),
            ObservationModel.observed_at.isnot(None),
        )
        results = list(self.session.scalars(stmt).all())

        # Apply sensor-specific threshold filtering in memory if required
        filtered: List[ObservationModel] = []
        for obs in results:
            if obs.sensor == "MODIS" and min_modis_confidence is not None:
                try:
                    conf = float(obs.confidence_raw) if obs.confidence_raw else 0.0
                    if conf < min_modis_confidence:
                        continue
                except ValueError:
                    pass
            elif obs.sensor == "VIIRS" and allowed_viirs_confidence_levels:
                conf_str = (obs.confidence_raw or "").lower()
                allowed_low = [c.lower() for c in allowed_viirs_confidence_levels]
                if conf_str not in allowed_low:
                    continue
            filtered.append(obs)

        return filtered


class ProcessingRunRepository:
    """Repository managing processing run lifecycle, candidates, and harmonised records."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, run_model: ProcessingRunModel) -> ProcessingRunModel:
        self.session.add(run_model)
        self.session.flush()
        return run_model

    def get(self, run_id: Union[str, uuid.UUID]) -> Optional[ProcessingRunModel]:
        uid = ensure_uuid(run_id)
        run = self.session.get(ProcessingRunModel, uid)
        if run:
            return run
        # Fallback query if string format is stored in input_dataset_ids or parameters
        stmt = select(ProcessingRunModel).filter(
            ProcessingRunModel.parameters["original_run_id"].as_string() == str(run_id)
        )
        return self.session.scalars(stmt).first()

    def list_all(self) -> List[ProcessingRunModel]:
        stmt = select(ProcessingRunModel).order_by(ProcessingRunModel.started_at.desc())
        return list(self.session.scalars(stmt).all())

    def update_status(
        self,
        run_id: Union[str, uuid.UUID],
        status: str,
        completed_at: Optional[datetime] = None,
        summary: Optional[dict] = None,
        error_summary: Optional[str] = None,
    ) -> None:
        run = self.get(run_id)
        if not run:
            return
        run.status = status
        if completed_at is not None:
            run.completed_at = completed_at
        if summary is not None:
            run.summary = summary
        if error_summary is not None:
            run.error_summary = error_summary
        self.session.flush()

    def save_results(
        self,
        run_id: Union[str, uuid.UUID],
        candidates: List[MatchCandidateModel],
        records: List[HarmonisedRecordModel],
        summary: dict,
    ) -> None:
        """Atomically persist match candidates, harmonised records, and success status."""
        run = self.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found.")

        self.session.add_all(candidates)
        self.session.add_all(records)
        run.status = "succeeded"
        run.completed_at = datetime.now(timezone.utc)
        run.summary = summary
        self.session.flush()

    def get_candidates(
        self,
        run_id: Union[str, uuid.UUID],
        limit: int = 1000,
        offset: int = 0,
    ) -> List[MatchCandidateModel]:
        uid = ensure_uuid(run_id)
        stmt = (
            select(MatchCandidateModel)
            .filter(MatchCandidateModel.run_id == uid)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def get_records(
        self,
        run_id: Union[str, uuid.UUID],
        match_status: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[HarmonisedRecordModel]:
        uid = ensure_uuid(run_id)
        stmt = select(HarmonisedRecordModel).filter(HarmonisedRecordModel.run_id == uid)
        if match_status:
            statuses = [s.strip() for s in match_status.split(",") if s.strip()]
            if statuses:
                stmt = stmt.filter(HarmonisedRecordModel.match_status.in_(statuses))

        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())

    def find_spatial_temporal_candidates(
        self,
        modis_dataset_id: Union[str, uuid.UUID],
        viirs_dataset_id: Union[str, uuid.UUID],
        max_distance_meters: float,
        max_time_difference_seconds: float,
        allowed_statuses: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute indexed spatial-temporal candidate search.
        Uses PostgreSQL PostGIS ST_DWithin + ST_Distance when running on PostgreSQL,
        or delegates to spatial indexing (STRtree / Geod) when on SQLite.
        """
        m_uid = ensure_uuid(modis_dataset_id)
        v_uid = ensure_uuid(viirs_dataset_id)
        statuses = tuple(allowed_statuses or ["valid", "warning"])

        is_postgres = (
            self.session.bind is not None
            and self.session.bind.dialect.name == "postgresql"
        )

        if is_postgres:
            raw_sql = text("""
                SELECT
                    m.id AS modis_observation_id,
                    v.id AS viirs_observation_id,
                    ST_Distance(m.geom, v.geom) AS spatial_distance_m,
                    ABS(EXTRACT(EPOCH FROM (v.observed_at - m.observed_at))) AS time_difference_s,
                    EXTRACT(EPOCH FROM (v.observed_at - m.observed_at)) AS signed_time_difference_s
                FROM observations m
                JOIN observations v
                  ON m.dataset_id = :modis_dataset_id
                 AND v.dataset_id = :viirs_dataset_id
                 AND m.sensor = 'MODIS'
                 AND v.sensor = 'VIIRS'
                 AND m.quality_status IN :allowed_statuses
                 AND v.quality_status IN :allowed_statuses
                 AND m.observed_at BETWEEN (v.observed_at - (:max_time_difference_seconds * INTERVAL '1 second'))
                                       AND (v.observed_at + (:max_time_difference_seconds * INTERVAL '1 second'))
                 AND ST_DWithin(m.geom, v.geom, :max_distance_meters)
                ORDER BY m.id, v.id;
            """)
            result = self.session.execute(
                raw_sql,
                {
                    "modis_dataset_id": m_uid,
                    "viirs_dataset_id": v_uid,
                    "allowed_statuses": statuses,
                    "max_distance_meters": max_distance_meters,
                    "max_time_difference_seconds": max_time_difference_seconds,
                },
            )
            return [dict(row._mapping) for row in result]

        # SQLite fallback: fetch observations and compute spatial-temporal candidate pairs
        m_stmt = select(ObservationModel).filter(
            ObservationModel.dataset_id == m_uid,
            ObservationModel.sensor == "MODIS",
            ObservationModel.quality_status.in_(statuses),
            ObservationModel.latitude.isnot(None),
            ObservationModel.longitude.isnot(None),
            ObservationModel.observed_at.isnot(None),
        )
        v_stmt = select(ObservationModel).filter(
            ObservationModel.dataset_id == v_uid,
            ObservationModel.sensor == "VIIRS",
            ObservationModel.quality_status.in_(statuses),
            ObservationModel.latitude.isnot(None),
            ObservationModel.longitude.isnot(None),
            ObservationModel.observed_at.isnot(None),
        )
        modis_list = list(self.session.scalars(m_stmt).all())
        viirs_list = list(self.session.scalars(v_stmt).all())

        candidates: List[Dict[str, Any]] = []
        for m in modis_list:
            for v in viirs_list:
                dt_s = (v.observed_at - m.observed_at).total_seconds()
                abs_dt_s = abs(dt_s)
                if abs_dt_s > max_time_difference_seconds:
                    continue

                dist_m = MatchingEngineService.haversine_distance_meters(
                    m.latitude, m.longitude, v.latitude, v.longitude
                )
                if dist_m <= max_distance_meters:
                    candidates.append({
                        "modis_observation_id": m.id,
                        "viirs_observation_id": v.id,
                        "spatial_distance_m": dist_m,
                        "time_difference_s": abs_dt_s,
                        "signed_time_difference_s": dt_s,
                    })

        candidates.sort(key=lambda c: (str(c["modis_observation_id"]), str(c["viirs_observation_id"])))
        return candidates
