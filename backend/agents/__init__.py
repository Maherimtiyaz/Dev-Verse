"""
Agents package for DevVerse AI

Exposes all agent classes for easy import.
"""

from backend.agents.base import (
    BaseAgent,
    AgentState,
    AgentResponse,
    AgentType,
    ToolResult,
)
from backend.agents.github_analyzer import (
    GitHubAnalyzerAgent,
    DeveloperDNA,
    GitHubAnalyzerState,
    GitHubTools,
)
from backend.agents.code_review import (
    CodeReviewAgent,
    CodeReviewReport,
    CodeReviewIssue,
    ReviewMode,
    ArchitectureReviewer,
    SecurityReviewer,
    PerformanceReviewer,
    RoastGenerator,
)
from backend.agents.matchmaking import (
    ProjectRecommendationAgent,
    HackathonPartnerAgent,
    ProjectMatch,
    ContributionRoadmap,
    PartnerMatch,
    TeamComposition,
    CompatibilityLevel,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentState",
    "AgentResponse",
    "AgentType",
    "ToolResult",
    # GitHub Analyzer
    "GitHubAnalyzerAgent",
    "DeveloperDNA",
    "GitHubAnalyzerState",
    "GitHubTools",
    # Code Review
    "CodeReviewAgent",
    "CodeReviewReport",
    "CodeReviewIssue",
    "ReviewMode",
    "ArchitectureReviewer",
    "SecurityReviewer",
    "PerformanceReviewer",
    "RoastGenerator",
    # Matchmaking
    "ProjectRecommendationAgent",
    "HackathonPartnerAgent",
    "ProjectMatch",
    "ContributionRoadmap",
    "PartnerMatch",
    "TeamComposition",
    "CompatibilityLevel",
]
