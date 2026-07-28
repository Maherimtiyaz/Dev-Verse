"""
DevVerse AI - Hackathon Teams Routes

Team formation and teammate matching endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import DbSession, CurrentUser
from models import HackathonTeam, TeamMember, User, Profile
from schemas import (
    TeamCreate,
    TeamResponse,
    TeamJoinRequest,
    TeammateMatch,
)

router = APIRouter()


@router.post(
    "/",
    response_model=TeamResponse,
    summary="Create hackathon team",
)
async def create_team(
    team_data: TeamCreate,
    current_user_id: CurrentUser,
    db: DbSession,
) -> TeamResponse:
    """
    Create a new hackathon team.
    """
    from uuid import UUID
    
    team = HackathonTeam(
        name=team_data.name,
        project_idea=team_data.project_idea,
        max_members=team_data.max_members,
        current_members=1,  # Creator is first member
    )
    db.add(team)
    await db.flush()
    
    # Add creator as first member
    member = TeamMember(
        team_id=team.id,
        user_id=UUID(current_user_id),
        role="founder",
    )
    db.add(member)
    
    await db.commit()
    await db.refresh(team)
    
    # Get profile for response
    result = await db.execute(
        select(Profile).where(Profile.user_id == UUID(current_user_id))
    )
    profile = result.scalar_one_or_none()
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        project_idea=team.project_idea,
        max_members=team.max_members,
        current_members=team.current_members,
        status=team.status,
        members=[],
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


@router.get(
    "/",
    response_model=list[TeamResponse],
    summary="List teams",
)
async def list_teams(
    db: DbSession,
) -> list[TeamResponse]:
    """
    Get all hackathon teams looking for members.
    """
    result = await db.execute(
        select(HackathonTeam).where(HackathonTeam.status == "forming")
    )
    teams = result.scalars().all()
    
    return [
        TeamResponse(
            id=team.id,
            name=team.name,
            project_idea=team.project_idea,
            max_members=team.max_members,
            current_members=team.current_members,
            status=team.status,
            members=[],
            created_at=team.created_at,
            updated_at=team.updated_at,
        )
        for team in teams
    ]


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get team details",
)
async def get_team(
    team_id: str,
    db: DbSession,
) -> TeamResponse:
    """
    Get details of a specific team.
    """
    from uuid import UUID
    
    result = await db.execute(
        select(HackathonTeam).where(HackathonTeam.id == UUID(team_id))
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        project_idea=team.project_idea,
        max_members=team.max_members,
        current_members=team.current_members,
        status=team.status,
        members=[],
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


@router.post(
    "/{team_id}/join",
    response_model=TeamResponse,
    summary="Join a team",
)
async def join_team(
    team_id: str,
    request: TeamJoinRequest,
    current_user_id: CurrentUser,
    db: DbSession,
) -> TeamResponse:
    """
    Join an existing hackathon team.
    """
    from uuid import UUID
    
    result = await db.execute(
        select(HackathonTeam).where(HackathonTeam.id == UUID(team_id))
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    
    if team.current_members >= team.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team is full",
        )
    
    if team.status != "forming":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team is not accepting members",
        )
    
    # Add member
    member = TeamMember(
        team_id=team.id,
        user_id=UUID(current_user_id),
        role=request.role,
    )
    db.add(member)
    
    team.current_members += 1
    if team.current_members >= team.max_members:
        team.status = "complete"
    
    await db.commit()
    await db.refresh(team)
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        project_idea=team.project_idea,
        max_members=team.max_members,
        current_members=team.current_members,
        status=team.status,
        members=[],
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


@router.get(
    "/teammates/match",
    response_model=list[TeammateMatch],
    summary="Find potential teammates",
)
async def find_teammates(
    current_user_id: CurrentUser,
    db: DbSession,
    limit: int = 10,
) -> list[TeammateMatch]:
    """
    Find potential teammates based on skill compatibility.
    
    Uses AI-powered matching algorithm.
    """
    from uuid import uuid4
    
    # TODO: Implement full AI-powered teammate matching
    # For now, return placeholder matches
    
    return [
        TeammateMatch(
            user_id=uuid4(),
            username=f"developer_{i}",
            compatibility_score=0.9 - (i * 0.1),
            shared_skills=["Python", "JavaScript"],
            complementary_skills=["React", "DevOps"],
            availability="available",
            github_profile=f"https://github.com/developer_{i}",
        )
        for i in range(1, min(limit + 1, 4))
    ]
