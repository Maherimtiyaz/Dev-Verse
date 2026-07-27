"""
API Routes for AI Agents

Endpoints for:
- GitHub analysis (Developer DNA)
- Code review (AI Roast)
- Project recommendations
- Hackathon partner matching
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user
from backend.models import User
from backend.agents import (
    GitHubAnalyzerAgent,
    CodeReviewAgent,
    ProjectRecommendationAgent,
    HackathonPartnerAgent,
    ReviewMode,
)


router = APIRouter(prefix="/agents", tags=["AI Agents"])


# ============== Request/Response Schemas ==============

class GitHubAnalysisRequest(BaseModel):
    """Request for GitHub analysis."""
    github_username: str = Field(..., description="GitHub username to analyze")
    include_private: bool = Field(default=False, description="Include private repos if authorized")


class GitHubAnalysisResponse(BaseModel):
    """Response from GitHub analysis."""
    success: bool
    dna: Optional[Dict[str, Any]] = None
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CodeReviewRequest(BaseModel):
    """Request for code review."""
    repository_url: Optional[str] = None
    code_files: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {path, content} objects"
    )
    mode: str = Field(default="professional", description="professional or roast")


class CodeReviewResponse(BaseModel):
    """Response from code review."""
    success: bool
    report: Optional[Dict[str, Any]] = None
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectRecommendationRequest(BaseModel):
    """Request for project recommendations."""
    user_skills: List[str] = Field(default_factory=list)
    user_interests: List[str] = Field(default_factory=list)
    experience_level: str = Field(default="mid")
    available_projects: Optional[List[Dict[str, Any]]] = None


class ProjectRecommendationResponse(BaseModel):
    """Response with project recommendations."""
    success: bool
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    roadmap: Optional[Dict[str, Any]] = None
    message: str


class PartnerMatchRequest(BaseModel):
    """Request for hackathon partner matching."""
    user_profile: Dict[str, Any] = Field(..., description="User's profile data")
    potential_partners: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of potential partners to match against"
    )
    hackathon_theme: Optional[str] = None
    duration_days: int = Field(default=3)


class PartnerMatchResponse(BaseModel):
    """Response with partner matches."""
    success: bool
    matches: List[Dict[str, Any]] = Field(default_factory=list)
    team_composition: Optional[Dict[str, Any]] = None
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============== Endpoints ==============

@router.post("/github-analyzer/analyze", response_model=GitHubAnalysisResponse)
async def analyze_github_profile(
    request: GitHubAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a GitHub profile and generate Developer DNA.
    
    This endpoint:
    1. Fetches user's repositories
    2. Analyzes commits and PRs
    3. Identifies coding patterns
    4. Generates skills, strengths, weaknesses assessment
    5. Provides learning recommendations
    
    **Gen-Z Feature:** Get your dev personality profile! 🔥
    """
    try:
        agent = GitHubAnalyzerAgent()
        
        input_data = {
            "github_username": request.github_username,
            "include_private": request.include_private,
            "user_id": str(current_user.id),
        }
        
        result = await agent.run(input_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.errors,
            )
        
        return GitHubAnalysisResponse(
            success=True,
            dna=result.data,
            message=result.message,
            metadata=result.metadata,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/code-review/review", response_model=CodeReviewResponse)
async def submit_code_review(
    request: CodeReviewRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Submit code for AI review.
    
    Choose between:
    - **Professional mode:** Detailed, constructive feedback
    - **Roast mode:** Gen-Z style funny roasts 💀
    
    Analyzes:
    - Architecture
    - Security
    - Performance
    - Code quality
    """
    try:
        # Validate input
        if not request.repository_url and not request.code_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either repository_url or code_files must be provided",
            )
        
        agent = CodeReviewAgent()
        
        review_mode = ReviewMode.ROAST if request.mode == "roast" else ReviewMode.PROFESSIONAL
        
        input_data = {
            "repository_url": request.repository_url,
            "code_files": request.code_files,
            "review_mode": review_mode,
            "user_id": str(current_user.id),
        }
        
        result = await agent.run(input_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.errors,
            )
        
        return CodeReviewResponse(
            success=True,
            report=result.data,
            message=result.message,
            metadata=result.metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code review failed: {str(e)}",
        )


@router.post("/project-recommendation/match", response_model=ProjectRecommendationResponse)
async def get_project_recommendations(
    request: ProjectRecommendationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get personalized open source project recommendations.
    
    Matches you with projects based on:
    - Your skills
    - Your interests
    - Experience level
    - Career goals
    
    Returns contribution roadmap with first issue suggestions! 🚀
    """
    try:
        agent = ProjectRecommendationAgent()
        
        input_data = {
            "user_skills": request.user_skills,
            "user_interests": request.user_interests,
            "experience_level": request.experience_level,
            "available_projects": request.available_projects or [],
            "user_id": str(current_user.id),
        }
        
        result = await agent.run(input_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.errors,
            )
        
        return ProjectRecommendationResponse(
            success=True,
            recommendations=result.data.get("recommendations", []),
            roadmap=result.data.get("roadmap"),
            message=result.message,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project recommendation failed: {str(e)}",
        )


@router.post("/hackathon-partner/match", response_model=PartnerMatchResponse)
async def find_hackathon_partners(
    request: PartnerMatchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Find compatible hackathon teammates.
    
    Matching algorithm considers:
    - Complementary skills
    - Shared interests
    - Availability overlap
    - Timezone compatibility
    - Collaboration style
    
    Returns ranked partner list with compatibility scores! 🎯
    """
    try:
        agent = HackathonPartnerAgent()
        
        input_data = {
            "user_profile": request.user_profile,
            "potential_partners": request.potential_partners,
            "hackathon_theme": request.hackathon_theme,
            "duration_days": request.duration_days,
            "user_id": str(current_user.id),
        }
        
        result = await agent.run(input_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.errors,
            )
        
        return PartnerMatchResponse(
            success=True,
            matches=result.data.get("matches", []),
            team_composition=result.data.get("team_composition"),
            message=result.message,
            metadata=result.metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Partner matching failed: {str(e)}",
        )


@router.get("/github-analyzer/dna/{github_username}")
async def get_cached_dna(
    github_username: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get cached Developer DNA for a GitHub username.
    
    Useful for checking previously analyzed profiles without re-running analysis.
    """
    # TODO: Implement caching with Redis
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Cached DNA retrieval not yet implemented",
    )


@router.get("/code-review/templates")
async def get_review_templates():
    """
    Get available code review templates.
    
    Templates for different project types:
    - FastAPI backend
    - React frontend
    - Full-stack applications
    - ML/AI projects
    """
    return {
        "templates": [
            {
                "id": "fastapi-backend",
                "name": "FastAPI Backend Review",
                "focus_areas": ["architecture", "security", "performance", "async_patterns"],
            },
            {
                "id": "react-frontend",
                "name": "React Frontend Review",
                "focus_areas": ["component_structure", "state_management", "performance", "accessibility"],
            },
            {
                "id": "fullstack",
                "name": "Full-Stack Application Review",
                "focus_areas": ["api_design", "database", "frontend", "deployment"],
            },
            {
                "id": "ml-project",
                "name": "ML/AI Project Review",
                "focus_areas": ["model_architecture", "data_pipeline", "evaluation", "deployment"],
            },
        ]
    }
