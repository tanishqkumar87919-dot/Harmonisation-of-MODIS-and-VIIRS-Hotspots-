"""FastAPI Application entrypoint with structured error handling and upload security."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import datasets, health, runs
from backend.app.config import settings
from backend.app.schemas.datasets import SensorType
from backend.app.services.ingestion import IngestionService
from backend.app.services.repository import repo
from backend.app.services.standardization import StandardizationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup lifespan hook:
    Preload curated sample test fixtures if repository has no datasets.
    """
    samples_dir = Path(__file__).resolve().parent.parent.parent / "data" / "samples"
    modis_sample = samples_dir / "modis_sample_north_india.csv"
    viirs_sample = samples_dir / "viirs_sample_north_india.csv"

    if modis_sample.exists() and not repo.get_dataset("sample-modis-001"):
        with open(modis_sample, "rb") as f:
            content = f.read()
        _, ds_m, df_m = IngestionService.inspect_and_validate(
            file_content=content,
            dataset_id="sample-modis-001",
            source_uri="data/samples/modis_sample_north_india.csv",
            explicit_sensor=SensorType.MODIS,
            product_name="MOD14_Terra_Collection_6_1",
            product_version="C6.1",
            is_test_fixture=True,
        )
        obs_m = StandardizationService.standardize_records(df_m, ds_m)
        repo.save_dataset(ds_m, obs_m, content)

    if viirs_sample.exists() and not repo.get_dataset("sample-viirs-001"):
        with open(viirs_sample, "rb") as f:
            content = f.read()
        _, ds_v, df_v = IngestionService.inspect_and_validate(
            file_content=content,
            dataset_id="sample-viirs-001",
            source_uri="data/samples/viirs_sample_north_india.csv",
            explicit_sensor=SensorType.VIIRS,
            product_name="VNP14IMGTDL_NPP_Collection_1",
            product_version="v1.0",
            is_test_fixture=True,
        )
        obs_v = StandardizationService.standardize_records(df_v, ds_v)
        repo.save_dataset(ds_v, obs_v, content)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Reproducible geospatial pipeline and API for standardizing, comparing, "
        "and matching active-fire hotspot observations from MODIS and VIIRS sensors."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Structured Error Handlers (NFR-01, NFR-04, docs/06_SYSTEM_ARCHITECTURE.md Section 5)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Structured handler for standard HTTP exceptions."""
    remediations: Dict[int, str] = {
        400: "Review query parameters or uploaded file format.",
        404: "Verify resource identifier.",
        413: f"Uploaded file exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        422: "Confirm CSV columns and values match docs/04_DATA_SOURCES_AND_DICTIONARY.md.",
        500: "Internal processing error. Inspect server logs for scientific traceback.",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "detail": exc.detail,
            "status_code": exc.status_code,
            "remediation": remediations.get(exc.status_code, "Inspect request and retry."),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Structured handler for Pydantic validation failures (422)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request Schema Validation Failed",
            "detail": exc.errors(),
            "status_code": 422,
            "remediation": "Verify request JSON body or uploaded form fields match expected schema.",
        },
    )


# Register routes with API prefix
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(datasets.router, prefix=settings.API_V1_PREFIX)
app.include_router(runs.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def get_root():
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "version": settings.APP_VERSION,
    }
