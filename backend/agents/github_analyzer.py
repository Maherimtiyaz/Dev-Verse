"""
GitHub Analyzer Agent

Analyzes GitHub repositories, commits, and pull requests to generate
developer DNA profiles including skills, strengths, weaknesses, and recommendations.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.agents.base import BaseAgent, AgentState, AgentResponse, ToolResult
from backend.core.config import settings


class DeveloperDNA(BaseModel):
    """Developer DNA profile structure."""
    skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    engineering_style: str = ""
    recommended_learning: List[str] = Field(default_factory=list)
    personality_traits: Dict[str, str] = Field(default_factory=dict)
    experience_level: str = "mid"
    primary_languages: List[str] = Field(default_factory=list)
    contribution_patterns: Dict[str, Any] = Field(default_factory=dict)


class GitHubAnalyzerState(AgentState):
    """Extended state for GitHub analyzer."""
    github_username: str
    repositories: List[Dict[str, Any]]
    commits: List[Dict[str, Any]]
    pull_requests: List[Dict[str, Any]]
    languages: Dict[str, int]
    dna: Optional[DeveloperDNA]


class GitHubTools:
    """Tools for GitHub analysis."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
    
    async def fetch_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """Fetch user's repositories."""
        # In production, this would call GitHub API
        # For now, return mock data structure
        return [
            {
                "name": "example-project",
                "language": "Python",
                "stars": 150,
                "forks": 30,
                "updated_at": datetime.now().isoformat(),
                "description": "An example project",
                "topics": ["python", "fastapi", "api"],
            }
        ]
    
    async def fetch_user_commits(
        self, 
        username: str, 
        repo: str,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Fetch user's commits from a repository."""
        return [
            {
                "sha": "abc123",
                "message": "feat: add new feature",
                "timestamp": datetime.now().isoformat(),
                "additions": 150,
                "deletions": 20,
                "files_changed": 5,
            }
        ]
    
    async def fetch_user_prs(
        self, 
        username: str, 
        repo: str
    ) -> List[Dict[str, Any]]:
        """Fetch user's pull requests."""
        return [
            {
                "number": 42,
                "title": "Add authentication system",
                "state": "merged",
                "created_at": datetime.now().isoformat(),
                "merged_at": datetime.now().isoformat(),
                "additions": 500,
                "deletions": 50,
                "files_changed": 15,
                "review_comments": 8,
            }
        ]
    
    async def analyze_language_usage(
        self, 
        repos: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Analyze programming language usage across repositories."""
        languages: Dict[str, int] = {}
        for repo in repos:
            lang = repo.get("language", "Unknown")
            languages[lang] = languages.get(lang, 0) + 1
        return languages


class GitHubAnalyzerAgent(BaseAgent):
    """
    AI Agent that analyzes GitHub activity to create developer profiles.
    
    Workflow:
    1. Fetch repositories
    2. Fetch commits and PRs
    3. Analyze patterns
    4. Generate DNA profile
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.3,  # Lower temp for consistent analysis
    ):
        super().__init__(
            name="GitHub Analyzer Agent",
            llm_model=llm_model,
            temperature=temperature,
        )
        self.tools = GitHubTools()
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.build_graph()
    
    def define_state(self) -> type:
        return GitHubAnalyzerState
    
    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        graph = StateGraph(GitHubAnalyzerState)
        
        # Add nodes
        graph.add_node("fetch_repos", self.fetch_repositories)
        graph.add_node("fetch_activity", self.fetch_activity)
        graph.add_node("analyze_patterns", self.analyze_patterns)
        graph.add_node("generate_dna", self.generate_dna)
        
        # Define edges
        graph.add_edge(START, "fetch_repos")
        graph.add_edge("fetch_repos", "fetch_activity")
        graph.add_edge("fetch_activity", "analyze_patterns")
        graph.add_edge("analyze_patterns", "generate_dna")
        graph.add_edge("generate_dna", END)
        
        self.graph = graph
        self.compiled_graph = graph.compile()
        return graph
    
    async def fetch_repositories(self, state: GitHubAnalyzerState) -> GitHubAnalyzerState:
        """Fetch user's repositories."""
        username = state.get("github_username", "")
        if not username:
            state["errors"].append("GitHub username not provided")
            return state
        
        try:
            repos = await self.tools.fetch_user_repos(username)
            state["repositories"] = repos
            state["current_step"] = "repos_fetched"
        except Exception as e:
            state["errors"].append(f"Failed to fetch repos: {str(e)}")
        
        return state
    
    async def fetch_activity(self, state: GitHubAnalyzerState) -> GitHubAnalyzerState:
        """Fetch commits and PRs for analysis."""
        username = state.get("github_username", "")
        repos = state.get("repositories", [])
        
        all_commits = []
        all_prs = []
        
        for repo in repos[:5]:  # Limit to 5 repos for efficiency
            repo_name = repo.get("name", "")
            commits = await self.tools.fetch_user_commits(username, repo_name)
            prs = await self.tools.fetch_user_prs(username, repo_name)
            all_commits.extend(commits)
            all_prs.extend(prs)
        
        state["commits"] = all_commits
        state["pull_requests"] = all_prs
        state["current_step"] = "activity_fetched"
        
        return state
    
    async def analyze_patterns(self, state: GitHubAnalyzerState) -> GitHubAnalyzerState:
        """Analyze coding patterns and language usage."""
        repos = state.get("repositories", [])
        languages = await self.tools.analyze_language_usage(repos)
        state["languages"] = languages
        state["current_step"] = "patterns_analyzed"
        return state
    
    async def generate_dna(self, state: GitHubAnalyzerState) -> GitHubAnalyzerState:
        """Generate developer DNA profile using LLM."""
        system_prompt = """You are an expert developer analyst. 
        Analyze the GitHub activity data and create a comprehensive developer DNA profile.
        Be specific, actionable, and honest in your assessment."""
        
        context = f"""
        GitHub Username: {state.get('github_username', 'unknown')}
        Repositories: {len(state.get('repositories', []))}
        Languages: {state.get('languages', {})}
        Commits: {len(state.get('commits', []))}
        Pull Requests: {len(state.get('pull_requests', []))}
        
        Recent Repos:
        {state.get('repositories', [])}
        
        Recent Commits:
        {state.get('commits', [])}
        
        Recent PRs:
        {state.get('pull_requests', [])}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate DeveloperDNA JSON for:\n{context}")
            ])
            
            # Parse the response into DeveloperDNA structure
            # In production, use structured output or function calling
            dna_data = {
                "skills": ["Python", "FastAPI", "REST APIs", "Async Programming"],
                "strengths": ["Clean code architecture", "API design", "Testing"],
                "weaknesses": ["Documentation could be improved", "More open source contributions needed"],
                "engineering_style": "Test-driven, modular, async-first",
                "recommended_learning": ["Kubernetes", "GraphQL", "System Design"],
                "personality_traits": {
                    "collaboration": "high",
                    "innovation": "medium-high",
                    "attention_to_detail": "high"
                },
                "experience_level": "mid-senior",
                "primary_languages": ["Python", "TypeScript"],
                "contribution_patterns": {
                    "commit_frequency": "regular",
                    "pr_size": "medium",
                    "review_engagement": "active"
                }
            }
            
            state["dna"] = DeveloperDNA(**dna_data)
            state["result"] = dna_data
            state["current_step"] = "dna_generated"
            
        except Exception as e:
            state["errors"].append(f"Failed to generate DNA: {str(e)}")
            state["current_step"] = "error"
        
        return state
    
    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Execute the GitHub analyzer workflow."""
        try:
            initial_state = self._initialize_state(input_data)
            initial_state["github_username"] = input_data.get("github_username", "")
            initial_state["repositories"] = []
            initial_state["commits"] = []
            initial_state["pull_requests"] = []
            initial_state["languages"] = {}
            initial_state["dna"] = None
            
            if not self.compiled_graph:
                self.build_graph()
            
            result = await self.compiled_graph.ainvoke(initial_state)
            
            if result.get("errors"):
                return AgentResponse(
                    success=False,
                    errors=result["errors"],
                    message="GitHub analysis failed",
                )
            
            return AgentResponse(
                success=True,
                data=result.get("result", {}),
                message="Developer DNA generated successfully",
                metadata={
                    "username": result.get("github_username"),
                    "repos_analyzed": len(result.get("repositories", [])),
                    "commits_analyzed": len(result.get("commits", [])),
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                errors=[str(e)],
                message="GitHub analysis failed",
            )
