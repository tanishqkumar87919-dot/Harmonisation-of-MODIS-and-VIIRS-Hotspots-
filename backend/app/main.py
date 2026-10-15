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
            content_m = f.read()
        df_m, _, checksum_m = IngestionService.parse_raw_csv(content_m, "modis_sample_north_india.csv")
        renamed_m, _ = IngestionService.normalize_column_names(df_m)
        _, ds_m, obs_m = StandardizationService.process_and_standardize(
            df_raw=renamed_m,
            dataset_id="sample-modis-001",
            sensor=SensorType.MODIS,
            product_name="MOD14_Terra_Collection_6_1",
            product_version="C6.1",
            source_uri="data/samples/modis_sample_north_india.csv",
            checksum=checksum_m,
            ingestion_run_id="ingest-sample-001",
            is_test_fixture=True,
        )
        repo.save_dataset(ds_m, obs_m, content_m)

    if viirs_sample.exists() and not repo.get_dataset("sample-viirs-001"):
        with open(viirs_sample, "rb") as f:
            content_v = f.read()
        df_v, _, checksum_v = IngestionService.parse_raw_csv(content_v, "viirs_sample_north_india.csv")
        renamed_v, _ = IngestionService.normalize_column_names(df_v)
        _, ds_v, obs_v = StandardizationService.process_and_standardize(
            df_raw=renamed_v,
            dataset_id="sample-viirs-001",
            sensor=SensorType.VIIRS,
            product_name="VNP14IMGTDL_NPP_Collection_1",
            product_version="v1.0",
            source_uri="data/samples/viirs_sample_north_india.csv",
            checksum=checksum_v,
            ingestion_run_id="ingest-sample-002",
            is_test_fixture=True,
        )
        repo.save_dataset(ds_v, obs_v, content_v)

    modis_fixture = samples_dir / "sample_modis_fixture.csv"
    viirs_fixture = samples_dir / "sample_viirs_fixture.csv"

    if modis_fixture.exists() and not repo.get_dataset("fixture-modis-001"):
        with open(modis_fixture, "rb") as f:
            content_fix_m = f.read()
        df_fix_m, _, checksum_fix_m = IngestionService.parse_raw_csv(content_fix_m, "sample_modis_fixture.csv")
        renamed_fix_m, _ = IngestionService.normalize_column_names(df_fix_m)
        _, ds_fix_m, obs_fix_m = StandardizationService.process_and_standardize(
            df_raw=renamed_fix_m,
            dataset_id="fixture-modis-001",
            sensor=SensorType.MODIS,
            product_name="MOD14_Terra_Collection_6_1",
            product_version="C6.1",
            source_uri="data/samples/sample_modis_fixture.csv",
            checksum=checksum_fix_m,
            ingestion_run_id="ingest-fixture-001",
            is_test_fixture=True,
        )
        repo.save_dataset(ds_fix_m, obs_fix_m, content_fix_m)

    if viirs_fixture.exists() and not repo.get_dataset("fixture-viirs-001"):
        with open(viirs_fixture, "rb") as f:
            content_fix_v = f.read()
        df_fix_v, _, checksum_fix_v = IngestionService.parse_raw_csv(content_fix_v, "sample_viirs_fixture.csv")
        renamed_fix_v, _ = IngestionService.normalize_column_names(df_fix_v)
        _, ds_fix_v, obs_fix_v = StandardizationService.process_and_standardize(
            df_raw=renamed_fix_v,
            dataset_id="fixture-viirs-001",
            sensor=SensorType.VIIRS,
            product_name="VNP14IMGTDL_NPP_Collection_1",
            product_version="v1.0",
            source_uri="data/samples/sample_viirs_fixture.csv",
            checksum=checksum_fix_v,
            ingestion_run_id="ingest-fixture-002",
            is_test_fixture=True,
        )
        repo.save_dataset(ds_fix_v, obs_fix_v, content_fix_v)

    if not repo.list_runs() and repo.get_dataset("fixture-modis-001") and repo.get_dataset("fixture-viirs-001"):
        from backend.app.schemas.common import AmbiguityPolicy
        from backend.app.schemas.matching import MatchingParameters, MatchingQualityFilters
        from backend.app.services.evaluation import EvaluationService
        from backend.app.services.matching_engine import MatchingEngineService

        ds_m_rec = repo.get_dataset("fixture-modis-001")
        ds_v_rec = repo.get_dataset("fixture-viirs-001")
        all_obs_m = repo.get_observations("fixture-modis-001")
        all_obs_v = repo.get_observations("fixture-viirs-001")

        params = MatchingParameters(
            max_distance_meters=1000.0,
            max_time_difference_seconds=1800.0,
            ambiguity_policy=AmbiguityPolicy.RETAIN_AMBIGUOUS,
            matching_method_version="v1.0.0-phase2-ref",
            quality_filters=MatchingQualityFilters(include_warnings=True),
        )
        eligible_m = StandardizationService.get_eligible_observations(all_obs_m, include_warnings=True)
        eligible_v = StandardizationService.get_eligible_observations(all_obs_v, include_warnings=True)

        engine_res = MatchingEngineService.run_harmonisation(
            run_id="run-fixture-001",
            modis_observations=eligible_m,
            viirs_observations=eligible_v,
            parameters=params,
            modis_input_count=ds_m_rec.total_rows,
            viirs_input_count=ds_v_rec.total_rows,
            modis_warning_count=ds_m_rec.warning_rows,
            viirs_warning_count=ds_v_rec.warning_rows,
            modis_rejected_count=ds_m_rec.rejected_rows,
            viirs_rejected_count=ds_v_rec.rejected_rows,
        )
        eval_res = EvaluationService.generate_evaluation(
            summary=engine_res.summary_report,
            records=engine_res.harmonised_records,
            modis_observations=eligible_m,
            viirs_observations=eligible_v,
        )
        repo.save_run(
            engine_res.summary_report,
            engine_res.harmonised_records,
            engine_res.match_candidates,
            eval_res,
        )

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
