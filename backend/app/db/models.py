"""SQLAlchemy 2.0 ORM models and database integrity constraints.

Adheres strictly to docs/04_DATA_SOURCES_AND_DICTIONARY.md and docs/07_DATABASE_SCHEMA.md.
Defines:
- DatasetModel (`datasets`)
- ObservationModel (`observations`)
- ProcessingRunModel (`processing_runs`)
- MatchCandidateModel (`match_candidates`)
- HarmonisedRecordModel (`harmonised_records`)
"""

import uuid
from datetime import datetime
from typing import Any, List, Optional
from geoalchemy2 import Geography, WKTElement
from geoalchemy2.elements import _SpatialElement
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Index,
    JSON,
    Text,
    UUID,
    event,
    inspect,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    """Declarative base class for satellite harmonisation ORM models."""
    pass


class CompatibleGeography(TypeDecorator):
    """
    Transparent Geography type decorator.
    Compiles to PostGIS `geography(POINT, 4326)` on PostgreSQL,
    and fallback `TEXT` on SQLite for lightning-fast test execution.
    """
    impl = Geography
    cache_ok = True

    def __init__(self, geometry_type: str = "POINT", srid: int = 4326, spatial_index: bool = False, **kwargs: Any):
        self.geo_type = Geography(
            geometry_type=geometry_type,
            srid=srid,
            spatial_index=spatial_index,
            **kwargs,
        )
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect is None:
            return self.geo_type
        if dialect.name == "sqlite":
            return dialect.type_descriptor(Text())
        return dialect.type_descriptor(self.geo_type)

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if dialect is not None and dialect.name == "sqlite":
            if value is None:
                return None
            if isinstance(value, _SpatialElement):
                return str(value.data)
            return str(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if dialect is not None and dialect.name == "sqlite":
            if value is None:
                return None
            return WKTElement(str(value), srid=self.geo_type.srid)
        return value


# Dialect-agnostic JSON storage: JSONB on PostgreSQL, JSON on SQLite
JsonType = JSONB().with_variant(JSON(), "sqlite")


class DatasetModel(Base):
    """
    Stores metadata for ingested satellite datasets (MODIS or VIIRS).
    Adheres to docs/07_DATABASE_SCHEMA.md Section 3.
    """
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    product_version: Mapped[str] = mapped_column(Text, nullable=False)
    source_uri: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)

    # Relationships
    observations: Mapped[List["ObservationModel"]] = relationship(
        "ObservationModel",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("sensor IN ('MODIS', 'VIIRS')", name="ck_datasets_sensor"),
    )


class ObservationModel(Base):
    """
    Raw and standardized satellite active fire observation.
    Adheres to docs/04_DATA_SOURCES_AND_DICTIONARY.md & docs/07_DATABASE_SCHEMA.md Section 3.
    """
    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_record_id: Mapped[str] = mapped_column(Text, nullable=False)
    sensor: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    geom: Mapped[Optional[Any]] = mapped_column(
        CompatibleGeography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )
    confidence_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frp_raw: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    frp_unit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_fields: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    quality_status: Mapped[str] = mapped_column(Text, nullable=False)
    quality_notes: Mapped[list] = mapped_column(JsonType, nullable=False, default=list)

    # Relationships
    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="observations")

    __table_args__ = (
        # Controlled sensors
        CheckConstraint("sensor IN ('MODIS', 'VIIRS')", name="ck_observations_sensor"),
        # Controlled quality statuses
        CheckConstraint("quality_status IN ('valid', 'warning', 'rejected')", name="ck_observations_quality_status"),
        # Range checks: mandatory unless rejected
        CheckConstraint(
            "quality_status = 'rejected' OR (latitude IS NOT NULL AND latitude >= -90.0 AND latitude <= 90.0)",
            name="ck_observations_latitude_range",
        ),
        CheckConstraint(
            "quality_status = 'rejected' OR (longitude IS NOT NULL AND longitude >= -180.0 AND longitude <= 180.0)",
            name="ck_observations_longitude_range",
        ),
        CheckConstraint(
            "quality_status = 'rejected' OR observed_at IS NOT NULL",
            name="ck_observations_valid_observed_at",
        ),
        # Indexes
        Index("ix_observations_dataset_id", "dataset_id"),
        Index("ix_observations_sensor_observed_at", "sensor", "observed_at"),
        Index("ix_observations_geom_gist", "geom", postgresql_using="gist"),
    )

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if self.geom is None and self.latitude is not None and self.longitude is not None:
            self.geom = WKTElement(f"POINT({self.longitude} {self.latitude})", srid=4326)


@event.listens_for(ObservationModel, "before_insert")
@event.listens_for(ObservationModel, "before_update")
def _populate_observation_geom(mapper: Any, connection: Any, target: ObservationModel) -> None:
    """Ensure spatial geometry column is populated for valid coordinate pairs."""
    if target.geom is None and target.latitude is not None and target.longitude is not None:
        target.geom = WKTElement(f"POINT({target.longitude} {target.latitude})", srid=4326)


@event.listens_for(ObservationModel, "before_update")
def _protect_raw_fields_immutability(mapper: Any, connection: Any, target: ObservationModel) -> None:
    """
    Enforce Rule 2 (docs/07_DATABASE_SCHEMA.md Section 2):
    Raw source fields and original observation attributes must remain immutable once recorded.
    """
    state = inspect(target)
    immutable_fields = ("raw_fields", "confidence_raw", "frp_raw", "frp_unit", "source_record_id")
    for field_name in immutable_fields:
        attr = state.attrs.get(field_name)
        if attr and attr.history.has_changes():
            raise ValueError(
                f"Integrity violation: Observation field '{field_name}' is immutable and cannot be overwritten."
            )


class ProcessingRunModel(Base):
    """
    Tracks execution metadata, parameters, and summary metrics for a harmonisation run.
    Adheres to docs/07_DATABASE_SCHEMA.md Section 3.
    """
    __tablename__ = "processing_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    method_version: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    input_dataset_ids: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    summary: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    match_candidates: Mapped[List["MatchCandidateModel"]] = relationship(
        "MatchCandidateModel",
        back_populates="run",
        cascade="all, delete-orphan",
    )
    harmonised_records: Mapped[List["HarmonisedRecordModel"]] = relationship(
        "HarmonisedRecordModel",
        back_populates="run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_processing_runs_status",
        ),
        Index("ix_processing_runs_status_started_at", "status", "started_at"),
    )


class MatchCandidateModel(Base):
    """
    Candidate spatial-temporal relationship between MODIS and VIIRS detections.
    Separates candidate discovery from final match classification (07_DATABASE_SCHEMA.md Section 3).
    """
    __tablename__ = "match_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processing_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    modis_observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("observations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    viirs_observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("observations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    spatial_distance_m: Mapped[float] = mapped_column(Double, nullable=False)
    time_difference_s: Mapped[float] = mapped_column(Double, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    run: Mapped["ProcessingRunModel"] = relationship("ProcessingRunModel", back_populates="match_candidates")
    modis_observation: Mapped["ObservationModel"] = relationship(
        "ObservationModel",
        foreign_keys=[modis_observation_id],
    )
    viirs_observation: Mapped["ObservationModel"] = relationship(
        "ObservationModel",
        foreign_keys=[viirs_observation_id],
    )

    __table_args__ = (
        CheckConstraint("spatial_distance_m >= 0.0", name="ck_match_candidates_distance_nonneg"),
        CheckConstraint("time_difference_s >= 0.0", name="ck_match_candidates_time_nonneg"),
        CheckConstraint(
            "decision IN ('accepted', 'rejected', 'ambiguous', 'pending')",
            name="ck_match_candidates_decision",
        ),
        Index("ix_match_candidates_run_decision", "run_id", "decision"),
    )


class HarmonisedRecordModel(Base):
    """
    Final harmonised hotspot record (matched, unmatched_modis, unmatched_viirs, ambiguous).
    Adheres strictly to docs/07_DATABASE_SCHEMA.md Section 3 & 4.
    """
    __tablename__ = "harmonised_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processing_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_status: Mapped[str] = mapped_column(Text, nullable=False)
    modis_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("observations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    viirs_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("observations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    attributes: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    provenance: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)

    # Relationships
    run: Mapped["ProcessingRunModel"] = relationship("ProcessingRunModel", back_populates="harmonised_records")
    modis_observation: Mapped[Optional["ObservationModel"]] = relationship(
        "ObservationModel",
        foreign_keys=[modis_observation_id],
    )
    viirs_observation: Mapped[Optional["ObservationModel"]] = relationship(
        "ObservationModel",
        foreign_keys=[viirs_observation_id],
    )

    __table_args__ = (
        CheckConstraint(
            "match_status IN ('matched', 'unmatched_modis', 'unmatched_viirs', 'ambiguous')",
            name="ck_harmonised_records_match_status",
        ),
        CheckConstraint(
            "(match_status = 'matched' AND modis_observation_id IS NOT NULL AND viirs_observation_id IS NOT NULL) OR "
            "(match_status = 'unmatched_modis' AND modis_observation_id IS NOT NULL AND viirs_observation_id IS NULL) OR "
            "(match_status = 'unmatched_viirs' AND viirs_observation_id IS NOT NULL AND modis_observation_id IS NULL) OR "
            "(match_status = 'ambiguous' AND (modis_observation_id IS NOT NULL OR viirs_observation_id IS NOT NULL))",
            name="ck_harmonised_records_source_links",
        ),
        Index("ix_harmonised_records_run_status", "run_id", "match_status"),
    )
