"""
DevVerse AI - Users Routes

User management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import DbSession, CurrentUser, Pagination
from models import User
from schemas import UserResponse

router = APIRouter()


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List users",
)
async def list_users(
    db: DbSession,
    pagination: Pagination,
) -> list[UserResponse]:
    """
    Get paginated list of users.
    """
    result = await db.execute(
        select(User)
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: str,
    db: DbSession,
) -> UserResponse:
    """
    Get a specific user by ID.
    """
    from uuid import UUID
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
    )
