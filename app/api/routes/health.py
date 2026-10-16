from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Liveness check. Dependency checks (DB, Redis, Claude) are added in later phases."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
    )
