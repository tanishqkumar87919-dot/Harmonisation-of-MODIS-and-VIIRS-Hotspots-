"""Database engine, session management, and PostGIS extension initialization.

Adheres to SQLAlchemy 2.0 best practices and docs/07_DATABASE_SCHEMA.md.
Provides seamless support for both PostgreSQL+PostGIS in production and SQLite in tests.
"""

import sqlite3
from typing import Generator
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import settings


def get_engine_args(url: str) -> dict:
    """Return dialect-appropriate engine arguments."""
    engine_kwargs: dict = {}
    if url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or url == "sqlite://":
            engine_kwargs["poolclass"] = StaticPool
    return engine_kwargs


@event.listens_for(Engine, "connect")
def _setup_sqlite_connection(dbapi_connection, connection_record):
    """
    Configure SQLite connection to enforce foreign keys and register
    geospatial stub functions so queries and geometry operations work
    seamlessly in fast in-memory test environments without SpatiaLite.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        # Register spatial helper functions matching PostGIS signatures
        dbapi_connection.create_function("ST_MakePoint", 2, lambda x, y: f"POINT({x} {y})")
        dbapi_connection.create_function("ST_SetSRID", 2, lambda g, s: g)
        dbapi_connection.create_function("ST_GeogFromText", -1, lambda *a: a[0] if a else "")
        dbapi_connection.create_function("ST_GeomFromText", -1, lambda *a: a[0] if a else "")

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_db_engine(database_url: str | None = None) -> Engine:
    """Create and return a configured SQLAlchemy 2.0 Engine."""
    url = database_url or settings.database_url or "sqlite:///:memory:"
    return create_engine(url, **get_engine_args(url))


engine: Engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db_extensions(engine_instance: Engine) -> None:
    """
    Initialize PostgreSQL extensions required by the schema (PostGIS and pgcrypto).
    Gracefully no-ops when running against SQLite.
    """
    if engine_instance.dialect.name == "postgresql":
        with engine_instance.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a managed database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
