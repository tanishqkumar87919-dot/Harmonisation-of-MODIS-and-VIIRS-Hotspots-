"""Initial schema for MODIS and VIIRS satellite active fire harmonisation.

Revision ID: 0001
Revises: None
Create Date: 2026-10-15 19:30:00.000000

Adheres to:
- docs/04_DATA_SOURCES_AND_DICTIONARY.md
- docs/07_DATABASE_SCHEMA.md
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # PostgreSQL PostGIS & pgcrypto extension setup
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    geom_col_type = (
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
        if is_postgres
        else sa.Text()
    )

    # 1. datasets
    op.create_table(
        "datasets",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("sensor", sa.Text(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("product_version", sa.Text(), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("metadata_json", json_type, nullable=False),
        sa.CheckConstraint("sensor IN ('MODIS', 'VIIRS')", name="ck_datasets_sensor"),
    )

    # 2. observations
    op.create_table(
        "observations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", sa.UUID(as_uuid=True), sa.ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=False),
        sa.Column("sensor", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latitude", sa.Double(), nullable=True),
        sa.Column("longitude", sa.Double(), nullable=True),
        sa.Column("geom", geom_col_type, nullable=True),
        sa.Column("confidence_raw", sa.Text(), nullable=True),
        sa.Column("frp_raw", sa.Double(), nullable=True),
        sa.Column("frp_unit", sa.Text(), nullable=True),
        sa.Column("raw_fields", json_type, nullable=False),
        sa.Column("quality_status", sa.Text(), nullable=False),
        sa.Column("quality_notes", json_type, nullable=False),
        sa.CheckConstraint("sensor IN ('MODIS', 'VIIRS')", name="ck_observations_sensor"),
        sa.CheckConstraint("quality_status IN ('valid', 'warning', 'rejected')", name="ck_observations_quality_status"),
        sa.CheckConstraint(
            "quality_status = 'rejected' OR (latitude IS NOT NULL AND latitude >= -90.0 AND latitude <= 90.0)",
            name="ck_observations_latitude_range",
        ),
        sa.CheckConstraint(
            "quality_status = 'rejected' OR (longitude IS NOT NULL AND longitude >= -180.0 AND longitude <= 180.0)",
            name="ck_observations_longitude_range",
        ),
        sa.CheckConstraint(
            "quality_status = 'rejected' OR observed_at IS NOT NULL",
            name="ck_observations_valid_observed_at",
        ),
    )
    op.create_index("ix_observations_dataset_id", "observations", ["dataset_id"])
    op.create_index("ix_observations_sensor_observed_at", "observations", ["sensor", "observed_at"])
    if is_postgres:
        op.create_index("ix_observations_geom_gist", "observations", ["geom"], postgresql_using="gist")
    else:
        op.create_index("ix_observations_geom_gist", "observations", ["geom"])

    # 3. processing_runs
    op.create_table(
        "processing_runs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("method_version", sa.Text(), nullable=False),
        sa.Column("parameters", json_type, nullable=False),
        sa.Column("input_dataset_ids", json_type, nullable=False),
        sa.Column("summary", json_type, nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('queued', 'running', 'succeeded', 'failed')", name="ck_processing_runs_status"),
    )
    op.create_index("ix_processing_runs_status_started_at", "processing_runs", ["status", "started_at"])

    # 4. match_candidates
    op.create_table(
        "match_candidates",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.UUID(as_uuid=True), sa.ForeignKey("processing_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("modis_observation_id", sa.UUID(as_uuid=True), sa.ForeignKey("observations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("viirs_observation_id", sa.UUID(as_uuid=True), sa.ForeignKey("observations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("spatial_distance_m", sa.Double(), nullable=False),
        sa.Column("time_difference_s", sa.Double(), nullable=False),
        sa.Column("score", sa.Double(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.CheckConstraint("spatial_distance_m >= 0.0", name="ck_match_candidates_distance_nonneg"),
        sa.CheckConstraint("time_difference_s >= 0.0", name="ck_match_candidates_time_nonneg"),
        sa.CheckConstraint("decision IN ('accepted', 'rejected', 'ambiguous', 'pending')", name="ck_match_candidates_decision"),
    )
    op.create_index("ix_match_candidates_run_decision", "match_candidates", ["run_id", "decision"])

    # 5. harmonised_records
    op.create_table(
        "harmonised_records",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.UUID(as_uuid=True), sa.ForeignKey("processing_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_status", sa.Text(), nullable=False),
        sa.Column("modis_observation_id", sa.UUID(as_uuid=True), sa.ForeignKey("observations.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("viirs_observation_id", sa.UUID(as_uuid=True), sa.ForeignKey("observations.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("attributes", json_type, nullable=False),
        sa.Column("provenance", json_type, nullable=False),
        sa.CheckConstraint(
            "match_status IN ('matched', 'unmatched_modis', 'unmatched_viirs', 'ambiguous')",
            name="ck_harmonised_records_match_status",
        ),
        sa.CheckConstraint(
            "(match_status = 'matched' AND modis_observation_id IS NOT NULL AND viirs_observation_id IS NOT NULL) OR "
            "(match_status = 'unmatched_modis' AND modis_observation_id IS NOT NULL AND viirs_observation_id IS NULL) OR "
            "(match_status = 'unmatched_viirs' AND viirs_observation_id IS NOT NULL AND modis_observation_id IS NULL) OR "
            "(match_status = 'ambiguous' AND (modis_observation_id IS NOT NULL OR viirs_observation_id IS NOT NULL))",
            name="ck_harmonised_records_source_links",
        ),
    )
    op.create_index("ix_harmonised_records_run_status", "harmonised_records", ["run_id", "match_status"])


def downgrade() -> None:
    op.drop_table("harmonised_records")
    op.drop_table("match_candidates")
    op.drop_table("processing_runs")
    op.drop_table("observations")
    op.drop_table("datasets")
