"""
DevVerse AI - Pydantic Schemas

Request/response schemas for API validation.
Separated from database models for flexibility.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# ============== Shared Schemas ==============

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ============== User Schemas ==============

class UserCreate(BaseSchema):
    """Schema for creating a new user."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    username: str = Field(min_length=3, max_length=100)


class UserUpdate(BaseSchema):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)


class UserResponse(BaseSchema):
    """Schema for user response."""
    id: UUID
    email: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Schema for user in database (includes sensitive fields)."""
    password_hash: Optional[str] = None
    github_id: Optional[int] = None
    is_superuser: bool


# ============== Profile Schemas ==============

class ProfileCreate(BaseSchema):
    """Schema for creating a profile."""
    username: str = Field(min_length=3, max_length=100)
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None


class ProfileUpdate(BaseSchema):
    """Schema for updating a profile."""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    availability_status: Optional[str] = None
    looking_for_work: Optional[bool] = None
    open_to_collaboration: Optional[bool] = None


class ProfileResponse(BaseSchema):
    """Schema for profile response."""
    id: UUID
    user_id: UUID
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    github_username: Optional[str]
    linkedin_url: Optional[str]
    twitter_handle: Optional[str]
    availability_status: str
    looking_for_work: bool
    open_to_collaboration: bool
    created_at: datetime
    updated_at: datetime


# ============== Token Schemas ==============

class Token(BaseSchema):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseSchema):
    """JWT token payload."""
    sub: str
    exp: datetime
    iat: datetime
    type: str


class RefreshToken(BaseSchema):
    """Refresh token request."""
    refresh_token: str


# ============== GitHub Repository Schemas ==============

class GitHubRepositoryResponse(BaseSchema):
    """Schema for GitHub repository response."""
    id: UUID
    user_id: UUID
    repo_id: int
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars_count: int
    forks_count: int
    private: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
    last_synced: Optional[datetime]


# ============== Skill Schemas ==============

class SkillBase(BaseSchema):
    """Base skill schema."""
    name: str
    category: str


class SkillResponse(SkillBase):
    """Schema for skill response."""
    id: UUID
    parent_skill_id: Optional[UUID] = None


class UserSkillCreate(BaseSchema):
    """Schema for adding a skill to user."""
    skill_id: UUID
    proficiency_level: int = Field(ge=1, le=5)
    years_experience: Optional[float] = None


class UserSkillResponse(BaseSchema):
    """Schema for user skill response."""
    user_id: UUID
    skill_id: UUID
    skill_name: str
    skill_category: str
    proficiency_level: int
    years_experience: Optional[float]
    last_used: Optional[datetime]


# ============== Developer DNA Schema (GitHub Twin Output) ==============

class DeveloperDNA(BaseSchema):
    """Developer DNA profile from GitHub analysis."""
    skills: List[str] = Field(description="List of identified skills")
    strengths: List[str] = Field(description="Developer strengths")
    weaknesses: List[str] = Field(description="Areas for improvement")
    engineering_style: str = Field(description="Engineering style description")
    recommended_learning: List[str] = Field(
        description="Recommended learning topics"
    )
    languages: Dict[str, int] = Field(
        default_factory=dict,
        description="Programming languages with usage percentage"
    )
    activity_score: float = Field(
        ge=0, le=100,
        description="Overall GitHub activity score"
    )


# ============== Code Review Schemas ==============

class CodeReviewRequest(BaseSchema):
    """Schema for requesting a code review."""
    repository_url: str
    review_type: str = Field(
        default="full",
        description="architecture/security/performance/roast/full"
    )
    roast_mode: bool = Field(default=False, description="Enable Gen-Z roast mode")


class CodeReviewFinding(BaseSchema):
    """Individual finding in a code review."""
    category: str
    severity: str = Field(description="critical/high/medium/low")
    title: str
    description: str
    recommendation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class CodeReviewResponse(BaseSchema):
    """Schema for code review response."""
    id: UUID
    repository_url: str
    review_type: str
    roast_mode: bool
    status: str
    overall_score: Optional[float] = None
    findings: List[CodeReviewFinding] = Field(default_factory=list)
    summary: Optional[str] = None
    roast_commentary: Optional[str] = None  # Only in roast mode
    created_at: datetime
    completed_at: Optional[datetime] = None


# ============== Project Matchmaking Schemas ==============

class ProjectMatchRequest(BaseSchema):
    """Schema for requesting project matches."""
    limit: int = Field(default=10, ge=1, le=100)
    difficulty_levels: Optional[List[str]] = None
    technologies: Optional[List[str]] = None


class ProjectMatch(BaseSchema):
    """Schema for a project match result."""
    project_id: UUID
    project_name: str
    description: Optional[str]
    github_url: Optional[str]
    technologies: Optional[Dict[str, Any]]
    difficulty_level: str
    match_score: float
    match_reasons: List[str]
    suggested_issues: Optional[List[Dict[str, Any]]] = None


class ProjectMatchResponse(BaseSchema):
    """Schema for project matching response."""
    matches: List[ProjectMatch]
    total_count: int


# ============== Hackathon Team Schemas ==============

class TeamCreate(BaseSchema):
    """Schema for creating a hackathon team."""
    name: str = Field(min_length=3, max_length=100)
    project_idea: Optional[str] = None
    max_members: int = Field(default=4, ge=2, le=10)
    required_skills: Optional[List[str]] = None


class TeamJoinRequest(BaseSchema):
    """Schema for joining a team."""
    role: str
    message: Optional[str] = None


class TeamMemberResponse(BaseSchema):
    """Schema for team member response."""
    user_id: UUID
    username: str
    role: str
    github_username: Optional[str]
    skills: List[str]
    joined_at: datetime


class TeamResponse(BaseSchema):
    """Schema for team response."""
    id: UUID
    name: str
    project_idea: Optional[str]
    max_members: int
    current_members: int
    status: str
    members: List[TeamMemberResponse]
    created_at: datetime
    updated_at: datetime


class TeammateMatch(BaseSchema):
    """Schema for teammate match result."""
    user_id: UUID
    username: str
    compatibility_score: float
    shared_skills: List[str]
    complementary_skills: List[str]
    availability: str
    github_profile: Optional[str]


# ============== Notification Schemas ==============

class NotificationResponse(BaseSchema):
    """Schema for notification response."""
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime


# ============== Health Check Schema ==============

class HealthCheck(BaseSchema):
    """Schema for health check response."""
    status: str
    version: str
    environment: str
    timestamp: datetime
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependent services"
    )
