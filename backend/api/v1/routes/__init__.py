"""
DevVerse AI - API v1 Routes

Route modules for API version 1.
"""

from api.v1.routes import (
    health,
    auth,
    users,
    profiles,
    github,
    code_reviews,
    projects,
    teams,
    agents,
)

__all__ = [
    "health",
    "auth",
    "users",
    "profiles",
    "github",
    "code_reviews",
    "projects",
    "teams",
    "agents",
]
