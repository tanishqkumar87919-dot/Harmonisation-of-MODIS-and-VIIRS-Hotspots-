"""Health check endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.schemas.run import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="Harmonisation of MODIS and VIIRS Hotspots API",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database_connected=True,
    )
