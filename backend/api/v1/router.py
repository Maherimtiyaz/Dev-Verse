"""
DevVerse AI - API v1 Router

Main router for API version 1.
Includes all feature endpoints.
"""

from fastapi import APIRouter

from api.v1.routes import (
    auth,
    users,
    profiles,
    github,
    code_reviews,
    projects,
    teams,
    health,
)


# Create API v1 router with prefix
api_router = APIRouter()

# Include all feature routers
api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    profiles.router,
    prefix="/profiles",
    tags=["Profiles"],
)

api_router.include_router(
    github.router,
    prefix="/github",
    tags=["GitHub Twin"],
)

api_router.include_router(
    code_reviews.router,
    prefix="/code-roast",
    tags=["Code Roast"],
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["Open Source Matchmaker"],
)

api_router.include_router(
    teams.router,
    prefix="/teams",
    tags=["Hackathon Teams"],
)
