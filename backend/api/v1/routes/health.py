"""
DevVerse AI - Health Check Endpoint

Basic health and readiness checks for the API.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, status

from core.config import settings
from schemas import HealthCheck

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def health_check() -> HealthCheck:
    """
    Basic health check endpoint.
    
    Returns application status and version information.
    """
    return HealthCheck(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def readiness_check() -> dict:
    """
    Readiness check for Kubernetes probes.
    
    Checks if all required services are available.
    """
    # TODO: Add actual service connectivity checks
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def liveness_check() -> dict:
    """
    Liveness check for Kubernetes probes.
    
    Simple endpoint to verify the application is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
