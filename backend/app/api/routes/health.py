"""Health check endpoint adhering to docs/06_SYSTEM_ARCHITECTURE.md."""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas.runs import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database_connected=True,
    )
