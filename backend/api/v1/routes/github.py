"""
DevVerse AI - GitHub Twin Routes

GitHub integration for developer profiling.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import DbSession, CurrentUser
from models import User, Profile, GitHubRepository
from schemas import DeveloperDNA, GitHubRepositoryResponse

router = APIRouter()


@router.get(
    "/sync",
    response_model=list[GitHubRepositoryResponse],
    summary="Sync GitHub repositories",
)
async def sync_github_repos(
    current_user_id: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> list[GitHubRepositoryResponse]:
    """
    Sync user's GitHub repositories.
    
    Fetches repositories from GitHub and stores them locally.
    This triggers a background task for full analysis.
    """
    from uuid import UUID
    import httpx
    from core.config import settings
    
    # Get user's GitHub username from profile
    result = await db.execute(
        select(Profile).where(Profile.user_id == UUID(current_user_id))
    )
    profile = result.scalar_one_or_none()
    
    if not profile or not profile.github_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub username not set in profile",
        )
    
    # Fetch repositories from GitHub API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/users/{profile.github_username}/repos",
            headers={"Accept": "application/vnd.github.v3+json"},
            params={"per_page": 100, "sort": "updated"},
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch repositories from GitHub",
            )
        
        repos = response.json()
    
    # Store/update repositories
    synced_repos = []
    for repo in repos:
        # Check if repo exists
        result = await db.execute(
            select(GitHubRepository).where(
                GitHubRepository.user_id == UUID(current_user_id),
                GitHubRepository.repo_id == repo["id"],
            )
        )
        existing_repo = result.scalar_one_or_none()
        
        if existing_repo:
            # Update existing
            existing_repo.name = repo["name"]
            existing_repo.full_name = repo["full_name"]
            existing_repo.description = repo.get("description")
            existing_repo.language = repo.get("language")
            existing_repo.stars_count = repo["stargazers_count"]
            existing_repo.forks_count = repo["forks_count"]
            existing_repo.private = repo["private"]
            existing_repo.archived = repo["archived"]
            synced_repos.append(existing_repo)
        else:
            # Create new
            new_repo = GitHubRepository(
                user_id=UUID(current_user_id),
                repo_id=repo["id"],
                name=repo["name"],
                full_name=repo["full_name"],
                description=repo.get("description"),
                language=repo.get("language"),
                stars_count=repo["stargazers_count"],
                forks_count=repo["forks_count"],
                private=repo["private"],
                archived=repo["archived"],
            )
            db.add(new_repo)
            synced_repos.append(new_repo)
    
    await db.commit()
    
    # Trigger background analysis
    # TODO: Add Celery task for full analysis
    # background_tasks.add_task(analyze_developer_dna, current_user_id)
    
    return [
        GitHubRepositoryResponse.model_validate(repo)
        for repo in synced_repos
    ]


@router.get(
    "/dna",
    response_model=DeveloperDNA,
    summary="Get Developer DNA",
)
async def get_developer_dna(
    current_user_id: CurrentUser,
    db: DbSession,
) -> DeveloperDNA:
    """
    Generate Developer DNA profile.
    
    Analyzes GitHub activity to create a comprehensive developer profile.
    Uses AI agents for deep analysis.
    """
    from uuid import UUID
    
    # Get user's repositories
    result = await db.execute(
        select(GitHubRepository).where(
            GitHubRepository.user_id == UUID(current_user_id)
        )
    )
    repos = result.scalars().all()
    
    if not repos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No repositories found. Please sync GitHub first.",
        )
    
    # TODO: Implement full AI-powered analysis using LangGraph agents
    # For now, return a basic analysis based on repository data
    
    languages = {}
    total_stars = 0
    total_forks = 0
    
    for repo in repos:
        if repo.language:
            languages[repo.language] = languages.get(repo.language, 0) + 1
        total_stars += repo.stars_count
        total_forks += repo.forks_count
    
    # Calculate top languages
    sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    top_languages = [lang[0] for lang in sorted_languages[:5]]
    
    # Generate basic DNA
    dna = DeveloperDNA(
        skills=top_languages,
        strengths=[
            "Active open source contributor" if total_stars > 10 else "Building projects",
            f"Proficient in {', '.join(top_languages[:3])}" if top_languages else "Learning",
        ],
        weaknesses=["Could contribute more to open source"],
        engineering_style="Full-stack developer with focus on practical solutions",
        recommended_learning=[
            "Consider exploring cloud technologies",
            "Deepen knowledge in system design",
        ],
        languages={lang: count for lang, count in sorted_languages},
        activity_score=min(100, len(repos) * 5 + total_stars * 2),
    )
    
    return dna


@router.get(
    "/repositories",
    response_model=list[GitHubRepositoryResponse],
    summary="Get my repositories",
)
async def get_my_repositories(
    current_user_id: CurrentUser,
    db: DbSession,
) -> list[GitHubRepositoryResponse]:
    """
    Get user's synced GitHub repositories.
    """
    from uuid import UUID
    
    result = await db.execute(
        select(GitHubRepository).where(
            GitHubRepository.user_id == UUID(current_user_id)
        )
    )
    repos = result.scalars().all()
    
    return [
        GitHubRepositoryResponse.model_validate(repo)
        for repo in repos
    ]
