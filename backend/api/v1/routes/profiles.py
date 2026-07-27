"""
DevVerse AI - Profiles Routes

User profile management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import DbSession, CurrentUser
from models import User, Profile
from schemas import ProfileResponse, ProfileUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Get my profile",
)
async def get_my_profile(
    current_user_id: CurrentUser,
    db: DbSession,
) -> ProfileResponse:
    """
    Get the authenticated user's profile.
    """
    from uuid import UUID
    
    result = await db.execute(
        select(Profile).where(Profile.user_id == UUID(current_user_id))
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    return ProfileResponse.model_validate(profile)


@router.put(
    "/me",
    response_model=ProfileResponse,
    summary="Update my profile",
)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user_id: CurrentUser,
    db: DbSession,
) -> ProfileResponse:
    """
    Update the authenticated user's profile.
    """
    from uuid import UUID
    
    result = await db.execute(
        select(Profile).where(Profile.user_id == UUID(current_user_id))
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    
    return ProfileResponse.model_validate(profile)


@router.get(
    "/{username}",
    response_model=ProfileResponse,
    summary="Get profile by username",
)
async def get_profile_by_username(
    username: str,
    db: DbSession,
) -> ProfileResponse:
    """
    Get a user's profile by username.
    """
    result = await db.execute(
        select(Profile).where(Profile.username == username)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    return ProfileResponse.model_validate(profile)
