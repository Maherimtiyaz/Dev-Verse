"""
DevVerse AI - Authentication Routes

JWT authentication and GitHub OAuth endpoints.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.security import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    validate_token,
)
from api.dependencies import DbSession, CurrentUser, OptionalUser
from models import User, Profile
from schemas import (
    UserCreate,
    UserResponse,
    Token,
    RefreshToken,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def register(
    user_data: UserCreate,
    db: DbSession,
) -> UserResponse:
    """
    Register a new user with email and password.
    
    Creates a user account and associated profile.
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username is taken (in profiles)
    result = await db.execute(
        select(Profile).where(Profile.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(user)
    
    # Flush to get user ID
    await db.flush()
    
    # Create profile
    profile = Profile(
        user_id=user.id,
        username=user_data.username,
    )
    db.add(profile)
    
    # Commit transaction
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Login with email/password",
)
async def login(
    email: str,
    password: str,
    db: DbSession,
) -> Token:
    """
    Authenticate user with email and password.
    
    Returns access and refresh tokens.
    """
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not pwd_context.verify(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    from datetime import datetime, timezone
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
)
async def refresh_token(
    token_data: RefreshToken,
) -> Token:
    """
    Refresh access token using refresh token.
    
    Requires valid refresh token.
    """
    user_id = validate_token(
        token_data.refresh_token,
        expected_type="refresh"
    )
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new tokens
    new_access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token(subject=user_id)
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
)
async def get_current_user_info(
    current_user_id: CurrentUser,
    db: DbSession,
) -> UserResponse:
    """
    Get information about the currently authenticated user.
    """
    from uuid import UUID
    
    result = await db.execute(
        select(User).where(User.id == UUID(current_user_id))
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


@router.get(
    "/github/login",
    summary="Initiate GitHub OAuth login",
)
async def github_login(request: Request):
    """
    Redirect to GitHub for OAuth authentication.
    
    Requires GITHUB_CLIENT_ID to be configured.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )
    
    # Generate state parameter for CSRF protection
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Store state in session (would use Redis in production)
    # For now, just include it in redirect
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"state={state}&"
        f"scope=user:email read:user repo"
    )
    
    return {"authorization_url": github_auth_url}


@router.get(
    "/github/callback",
    response_model=Token,
    summary="GitHub OAuth callback",
)
async def github_callback(
    code: str,
    state: str,
    request: Request,
    db: DbSession,
):
    """
    Handle GitHub OAuth callback.
    
    Exchanges code for access token and creates/updates user.
    """
    import httpx
    
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
                "state": state,
            },
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get GitHub access token",
            )
        
        token_data = token_response.json()
        github_access_token = token_data.get("access_token")
    
    # Get GitHub user info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {github_access_token}",
                "Accept": "application/json",
            },
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get GitHub user info",
            )
        
        github_user = user_response.json()
    
    # Get email (may require additional API call)
    email = github_user.get("email")
    if not email:
        async with httpx.AsyncClient() as client:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"token {github_access_token}",
                    "Accept": "application/json",
                },
            )
            if emails_response.status_code == 200:
                emails = emails_response.json()
                for e in emails:
                    if e.get("primary"):
                        email = e.get("email")
                        break
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve email from GitHub",
        )
    
    # Find or create user
    result = await db.execute(
        select(User).where(User.github_id == github_user["id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Check if email is already registered
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Link GitHub account to existing user
            user.github_id = github_user["id"]
        else:
            # Create new user
            import secrets
            user = User(
                email=email,
                github_id=github_user["id"],
                password_hash=get_password_hash(secrets.token_urlsafe(32)),
            )
            db.add(user)
            await db.flush()
            
            # Create profile
            profile = Profile(
                user_id=user.id,
                username=github_user["login"],
                full_name=github_user.get("name"),
                avatar_url=github_user.get("avatar_url"),
                bio=github_user.get("bio"),
                location=github_user.get("location"),
                website=github_user.get("blog"),
                github_username=github_user["login"],
            )
            db.add(profile)
    else:
        # Update existing user's GitHub info
        result = await db.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.avatar_url = github_user.get("avatar_url")
            profile.full_name = github_user.get("name")
            profile.bio = github_user.get("bio")
            profile.location = github_user.get("location")
            profile.website = github_user.get("blog")
    
    # Update last login
    from datetime import datetime, timezone
    user.last_login = datetime.now(timezone.utc)
    
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
