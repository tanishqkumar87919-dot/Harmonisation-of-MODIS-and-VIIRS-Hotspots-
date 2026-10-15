"""FastAPI Application entrypoint for Harmonisation of MODIS and VIIRS Hotspots."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import datasets, health, runs
from backend.app.schemas.common import SensorType
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
    title="Harmonisation of MODIS and VIIRS Hotspots API",
    description=(
        "Reproducible geospatial pipeline and API for standardizing, comparing, "
        "and matching active-fire hotspot observations from MODIS and VIIRS sensors."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(runs.router, prefix="/api")


@app.get("/")
def get_root():
    return {
        "service": "Harmonisation of MODIS and VIIRS Hotspots API",
        "docs": "/docs",
        "health": "/api/health",
        "version": "1.0.0",
    }
