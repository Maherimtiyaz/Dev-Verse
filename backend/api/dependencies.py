"""
DevVerse AI - API Dependencies

Common dependencies used across API endpoints:
- Database session
- Authentication
- Rate limiting
- Pagination
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.logging_config import get_logger, set_correlation_id
from core.security import validate_token
from db.session import get_db
import redis.asyncio as redis


logger = get_logger(__name__)


# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


# ============== Database Dependency ==============

async def get_database_session() -> AsyncSession:
    """Get database session from dependency."""
    async for session in get_db():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_database_session)]


# ============== Authentication Dependencies ==============

async def get_current_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> str:
    """
    Extract and validate user ID from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User ID from token subject
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user_id = validate_token(token, expected_type="access")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


CurrentUser = Annotated[str, Depends(get_current_user_id)]


async def get_optional_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[str]:
    """
    Get user ID if authenticated, None otherwise.
    
    Useful for endpoints that work differently for authenticated users.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    return validate_token(token, expected_type="access")


OptionalUser = Annotated[Optional[str], Depends(get_optional_user_id)]


# ============== Redis Dependency ==============

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    
    return _redis_client


RedisClient = Annotated[redis.Redis, Depends(get_redis)]


# ============== Rate Limiting ==============

async def rate_limit_checker(
    request: Request,
    redis_client: RedisClient,
    limit: int = settings.RATE_LIMIT_PER_MINUTE,
) -> None:
    """
    Check if request exceeds rate limit.
    
    Uses sliding window algorithm with Redis.
    
    Args:
        request: FastAPI request object
        redis_client: Redis client
        limit: Maximum requests per minute
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    # Get client identifier (user ID or IP)
    try:
        user_id = await get_optional_user_id(
            HTTPBearer(auto_error=False)(request)
        )
        identifier = user_id or request.client.host
    except Exception:
        identifier = request.client.host
    
    key = f"rate_limit:{identifier}:{request.url.path}"
    
    # Increment counter
    current = await redis_client.incr(key)
    
    if current == 1:
        # Set expiry on first request
        await redis_client.expire(key, 60)
    
    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per minute.",
        )


# ============== Correlation ID Middleware ==============

async def correlation_id_middleware(
    request: Request,
    call_next,
):
    """
    Middleware to handle correlation IDs for tracing.
    
    Extracts correlation ID from headers or generates new one.
    """
    from uuid import uuid4
    
    # Get or generate correlation ID
    correlation_id = request.headers.get(
        "X-Correlation-ID",
        str(uuid4())
    )
    
    # Set in context for logging
    set_correlation_id(correlation_id)
    
    # Process request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


# ============== Pagination ==============

class PaginationParams:
    """Pagination parameters."""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
    ):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))
        self.offset = (self.page - 1) * self.page_size


async def pagination(
    page: int = 1,
    page_size: int = 20,
) -> PaginationParams:
    """Get pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)


Pagination = Annotated[PaginationParams, Depends(pagination)]
