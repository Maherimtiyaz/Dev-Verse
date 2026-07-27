"""
DevVerse AI - SQLAlchemy Models

Database models following the schema design from ARCHITECTURE.md.
Uses UUID primary keys and proper relationships.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    validates,
)

from db.session import Base


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """User model for authentication and profiles."""
    
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    repositories: Mapped[List["GitHubRepository"]] = relationship(
        "GitHubRepository",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    skills: Mapped[List["UserSkill"]] = relationship(
        "UserSkill",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    code_reviews: Mapped[List["CodeReview"]] = relationship(
        "CodeReview",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    contributions: Mapped[List["Contribution"]] = relationship(
        "Contribution",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Profile(Base):
    """Extended user profile information."""
    
    __tablename__ = "profiles"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    github_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    twitter_handle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    availability_status: Mapped[str] = mapped_column(
        String(50),
        default="available"
    )
    looking_for_work: Mapped[bool] = mapped_column(Boolean, default=False)
    open_to_collaboration: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="profile")
    
    __table_args__ = (
        Index("idx_profiles_username", "username"),
        Index("idx_profiles_github", "github_username"),
    )
    
    def __repr__(self) -> str:
        return f"<Profile(username={self.username})>"


class GitHubRepository(Base):
    """GitHub repository metadata."""
    
    __tablename__ = "github_repositories"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    repo_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    stars_count: Mapped[int] = mapped_column(Integer, default=0)
    forks_count: Mapped[int] = mapped_column(Integer, default=0)
    private: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="repositories")
    
    __table_args__ = (
        UniqueConstraint("user_id", "repo_id", name="uq_user_repo"),
        Index("idx_repos_language", "language"),
    )
    
    def __repr__(self) -> str:
        return f"<GitHubRepository(full_name={self.full_name})>"


class Skill(Base):
    """Master list of skills."""
    
    __tablename__ = "skills"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="language, framework, tool, domain"
    )
    parent_skill_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationships
    parent_skill: Mapped[Optional["Skill"]] = relationship(
        "Skill",
        remote_side=[id],
        backref="child_skills"
    )
    user_skills: Mapped[List["UserSkill"]] = relationship(
        "UserSkill",
        back_populates="skill",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Skill(name={self.name})>"


class UserSkill(Base):
    """User's skills with proficiency levels."""
    
    __tablename__ = "user_skills"
    
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True
    )
    proficiency_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="1-5 scale"
    )
    years_experience: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="user_skills")
    
    def __repr__(self) -> str:
        return f"<UserSkill(user_id={self.user_id}, skill={self.skill.name})>"


class Project(Base):
    """Open source projects for matching."""
    
    __tablename__ = "projects"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    technologies: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    difficulty_level: Mapped[str] = mapped_column(
        String(20),
        default="intermediate",
        comment="beginner/intermediate/advanced"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="active/completed/archived"
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        nullable=True,
        comment="Vector embedding for semantic search"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )
    
    __table_args__ = (
        Index("idx_projects_difficulty", "difficulty_level"),
        Index("idx_projects_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Project(name={self.name})>"


class Match(Base):
    """Matches between users and projects/users."""
    
    __tablename__ = "matches"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="project/user"
    )
    target_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    match_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="pending/accepted/rejected"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    __table_args__ = (
        Index("idx_matches_user_target", "user_id", "target_type", "target_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Match(user_id={self.user_id}, target={self.target_type})>"


class CodeReview(Base):
    """Code review results from AI agents."""
    
    __tablename__ = "code_reviews"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    repository_url: Mapped[str] = mapped_column(String(512), nullable=False)
    review_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="architecture/security/performance/roast"
    )
    findings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    roast_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="pending/completed/failed"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="code_reviews")
    
    __table_args__ = (
        Index("idx_reviews_user_type", "user_id", "review_type"),
    )
    
    def __repr__(self) -> str:
        return f"<CodeReview(type={self.review_type})>"


class Contribution(Base):
    """Track user contributions to projects."""
    
    __tablename__ = "contributions"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="pr/issue/comment"
    )
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="contributions")
    
    def __repr__(self) -> str:
        return f"<Contribution(type={self.type})>"


class Notification(Base):
    """User notifications."""
    
    __tablename__ = "notifications"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    
    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "read"),
    )
    
    def __repr__(self) -> str:
        return f"<Notification(type={self.type})>"


class HackathonTeam(Base):
    """Hackathon teams for partner matching."""
    
    __tablename__ = "hackathon_teams"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_idea: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_members: Mapped[int] = mapped_column(Integer, default=4)
    current_members: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(20),
        default="forming",
        comment="forming/complete/disbanded"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )
    
    # Relationships
    members: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<HackathonTeam(name={self.name})>"


class TeamMember(Base):
    """Members of hackathon teams."""
    
    __tablename__ = "team_members"
    
    team_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("hackathon_teams.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationships
    team: Mapped["HackathonTeam"] = relationship("HackathonTeam", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")
    
    def __repr__(self) -> str:
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id})>"
