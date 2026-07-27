"""
Matchmaking Agent - Open Source Project & Hackathon Partner Matching

Two specialized agents:
1. ProjectRecommendationAgent - Matches developers with open source projects
2. HackathonPartnerAgent - Finds compatible hackathon teammates

Uses semantic similarity, skill matching, and compatibility scoring.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.agents.base import BaseAgent, AgentState, AgentResponse


# ============== PROJECT RECOMMENDATION AGENT ==============

class ProjectMatch(BaseModel):
    """Recommended project match."""
    project_id: str
    project_name: str
    repository_url: str
    match_score: float = Field(ge=0, le=1)
    reasons: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    difficulty: str = "medium"
    estimated_time_hours: int = 10
    first_issue_suggestions: List[Dict[str, Any]] = Field(default_factory=list)


class ContributionRoadmap(BaseModel):
    """Suggested contribution path."""
    week_1: List[str] = Field(default_factory=list)
    week_2: List[str] = Field(default_factory=list)
    week_3: List[str] = Field(default_factory=list)
    week_4: List[str] = Field(default_factory=list)
    long_term_goals: List[str] = Field(default_factory=list)


class ProjectRecommendationState(AgentState):
    """State for project recommendation agent."""
    user_skills: List[str]
    user_interests: List[str]
    user_experience_level: str
    available_projects: List[Dict[str, Any]]
    project_embeddings: Optional[List[Dict[str, Any]]]
    recommendations: List[ProjectMatch]
    roadmap: Optional[ContributionRoadmap]


class ProjectEmbeddingService:
    """Handles project embeddings and semantic search."""
    
    def __init__(self, qdrant_url: Optional[str] = None, api_key: Optional[str] = None):
        self.qdrant_url = qdrant_url
        self.api_key = api_key
        # In production: initialize Qdrant client
        # from qdrant_client import QdrantClient
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text."""
        # In production: call embedding model
        # For now, return mock embedding
        return [0.1] * 384  # Mock 384-dim embedding
    
    async def semantic_search(
        self, 
        query_embedding: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar projects using embeddings."""
        # In production: query Qdrant
        return []
    
    async def store_project_embedding(
        self, 
        project_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """Store project embedding in vector database."""
        # In production: upsert to Qdrant
        return True


class ProjectRecommendationAgent(BaseAgent):
    """
    AI Agent that matches developers with open source projects.
    
    Uses:
    - Skill similarity matching
    - Interest alignment
    - Difficulty assessment
    - Career goal consideration
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.3,
    ):
        super().__init__(
            name="Project Recommendation Agent",
            llm_model=llm_model,
            temperature=temperature,
        )
        self.embedding_service = ProjectEmbeddingService()
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.build_graph()
    
    def define_state(self) -> type:
        return ProjectRecommendationState
    
    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        graph = StateGraph(ProjectRecommendationState)
        
        # Add nodes
        graph.add_node("compute_user_embedding", self.compute_user_embedding)
        graph.add_node("find_matching_projects", self.find_matching_projects)
        graph.add_node("score_and_rank", self.score_and_rank_projects)
        graph.add_node("generate_recommendations", self.generate_recommendations)
        graph.add_node("create_roadmap", self.create_contribution_roadmap)
        
        # Define edges
        graph.add_edge(START, "compute_user_embedding")
        graph.add_edge("compute_user_embedding", "find_matching_projects")
        graph.add_edge("find_matching_projects", "score_and_rank")
        graph.add_edge("score_and_rank", "generate_recommendations")
        graph.add_edge("generate_recommendations", "create_roadmap")
        graph.add_edge("create_roadmap", END)
        
        self.graph = graph
        self.compiled_graph = graph.compile()
        return graph
    
    async def compute_user_embedding(self, state: ProjectRecommendationState) -> ProjectRecommendationState:
        """Create embedding from user profile."""
        user_skills = state.get("user_skills", [])
        user_interests = state.get("user_interests", [])
        
        # Create text representation of user profile
        profile_text = f"Skills: {', '.join(user_skills)}. Interests: {', '.join(user_interests)}."
        
        try:
            embedding = await self.embedding_service.create_embedding(profile_text)
            state["context"]["user_embedding"] = embedding
            state["current_step"] = "embedding_computed"
        except Exception as e:
            state["errors"].append(f"Embedding failed: {str(e)}")
        
        return state
    
    async def find_matching_projects(self, state: ProjectRecommendationState) -> ProjectRecommendationState:
        """Find projects matching user profile."""
        user_embedding = state.get("context", {}).get("user_embedding", [])
        
        if not user_embedding:
            # Fallback to non-semantic matching
            state["data"]["candidate_projects"] = state.get("available_projects", [])[:10]
            state["current_step"] = "projects_found_fallback"
            return state
        
        try:
            # Semantic search for similar projects
            matches = await self.embedding_service.semantic_search(user_embedding, limit=10)
            state["data"]["candidate_projects"] = matches
            state["current_step"] = "projects_found"
        except Exception as e:
            state["errors"].append(f"Project search failed: {str(e)}")
            state["data"]["candidate_projects"] = state.get("available_projects", [])[:10]
        
        return state
    
    async def score_and_rank_projects(self, state: ProjectRecommendationState) -> ProjectRecommendationState:
        """Score and rank candidate projects."""
        user_skills = set(state.get("user_skills", []))
        candidate_projects = state.get("data", {}).get("candidate_projects", [])
        
        scored_projects = []
        for project in candidate_projects:
            project_skills = set(project.get("technologies", []))
            
            # Calculate skill overlap
            matched = user_skills.intersection(project_skills)
            overlap_score = len(matched) / max(len(user_skills.union(project_skills)), 1)
            
            # Add interest alignment (simplified)
            interest_bonus = 0.1 if any(
                interest in project.get("topics", [])
                for interest in state.get("user_interests", [])
            ) else 0
            
            total_score = min(overlap_score + interest_bonus, 1.0)
            
            scored_projects.append({
                **project,
                "match_score": total_score,
                "matched_skills": list(matched),
            })
        
        # Sort by score descending
        scored_projects.sort(key=lambda x: x["match_score"], reverse=True)
        state["data"]["scored_projects"] = scored_projects
        state["current_step"] = "projects_scored"
        
        return state
    
    async def generate_recommendations(self, state: ProjectRecommendationState) -> ProjectRecommendationState:
        """Generate final project recommendations."""
        scored_projects = state.get("data", {}).get("scored_projects", [])
        
        recommendations = []
        for proj in scored_projects[:5]:  # Top 5 recommendations
            rec = ProjectMatch(
                project_id=proj.get("id", "unknown"),
                project_name=proj.get("name", "Unknown Project"),
                repository_url=proj.get("repository_url", ""),
                match_score=proj.get("match_score", 0),
                reasons=[
                    f"Matches {len(proj.get('matched_skills', []))} of your skills",
                    f"Uses technologies you know: {', '.join(proj.get('matched_skills', [])[:3])}",
                    f"Good fit for {state.get('user_experience_level', 'your')} level",
                ],
                required_skills=proj.get("technologies", []),
                matched_skills=proj.get("matched_skills", []),
                difficulty=proj.get("difficulty", "medium"),
                estimated_time_hours=proj.get("estimated_effort", 10),
                first_issue_suggestions=proj.get("good_first_issues", [])[:3],
            )
            recommendations.append(rec)
        
        state["recommendations"] = recommendations
        state["result"] = [r.model_dump() for r in recommendations]
        state["current_step"] = "recommendations_generated"
        
        return state
    
    async def create_contribution_roadmap(self, state: ProjectRecommendationState) -> ProjectRecommendationState:
        """Create a contribution roadmap for top recommendation."""
        recommendations = state.get("recommendations", [])
        
        if not recommendations:
            state["current_step"] = "complete"
            return state
        
        top_project = recommendations[0]
        
        # Generate roadmap using LLM
        system_prompt = """You are an open source mentor creating contribution roadmaps.
        Create a realistic 4-week plan for contributing to an open source project.
        Include specific, actionable steps."""
        
        context = f"""
        Project: {top_project.project_name}
        Skills: {top_project.matched_skills}
        Difficulty: {top_project.difficulty}
        """
        
        try:
            roadmap = ContributionRoadmap(
                week_1=["Set up development environment", "Read contribution guidelines", "Explore codebase structure"],
                week_2=["Fix a good first issue", "Join project community channels", "Attend maintainer office hours"],
                week_3=["Tackle a medium difficulty issue", "Submit first PR", "Engage in code review"],
                week_4=["Work on a feature request", "Help another new contributor", "Plan long-term contributions"],
                long_term_goals=[
                    "Become a regular contributor",
                    "Help triage issues",
                    "Consider becoming a maintainer"
                ]
            )
            state["roadmap"] = roadmap
            state["current_step"] = "roadmap_created"
        except Exception as e:
            state["errors"].append(f"Roadmap creation failed: {str(e)}")
        
        return state
    
    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Execute the project recommendation workflow."""
        try:
            initial_state = self._initialize_state(input_data)
            initial_state["user_skills"] = input_data.get("user_skills", [])
            initial_state["user_interests"] = input_data.get("user_interests", [])
            initial_state["user_experience_level"] = input_data.get("experience_level", "mid")
            initial_state["available_projects"] = input_data.get("available_projects", [])
            initial_state["project_embeddings"] = None
            initial_state["recommendations"] = []
            initial_state["roadmap"] = None
            
            if not self.compiled_graph:
                self.build_graph()
            
            result = await self.compiled_graph.ainvoke(initial_state)
            
            if result.get("errors"):
                return AgentResponse(
                    success=False,
                    errors=result["errors"],
                    message="Project recommendation failed",
                )
            
            return AgentResponse(
                success=True,
                data={
                    "recommendations": result.get("result", []),
                    "roadmap": result.get("roadmap").model_dump() if result.get("roadmap") else None,
                },
                message=f"Found {len(result.get('recommendations', []))} project matches",
                metadata={
                    "projects_analyzed": len(result.get("available_projects", [])),
                    "top_match_score": result["recommendations"][0].match_score if result.get("recommendations") else 0,
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                errors=[str(e)],
                message="Project recommendation failed",
            )


# ============== HACKATHON PARTNER AGENT ==============

class CompatibilityLevel(str, Enum):
    """Partner compatibility levels."""
    PERFECT = "perfect"
    HIGH = "high"
    GOOD = "good"
    FAIR = "fair"
    LOW = "low"


class PartnerMatch(BaseModel):
    """Hackathon partner match."""
    user_id: str
    username: str
    compatibility_score: float = Field(ge=0, le=1)
    compatibility_level: CompatibilityLevel
    complementary_skills: List[str] = Field(default_factory=list)
    shared_interests: List[str] = Field(default_factory=list)
    availability_overlap: str = ""
    timezone_diff_hours: int = 0
    previous_hackathons: int = 0
    strengths: List[str] = Field(default_factory=list)
    collaboration_style: str = ""


class TeamComposition(BaseModel):
    """Recommended team composition."""
    ideal_size: int = 4
    roles_needed: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    recommended_partners: List[PartnerMatch] = Field(default_factory=list)


class HackathonPartnerState(AgentState):
    """State for hackathon partner agent."""
    user_profile: Dict[str, Any]
    potential_partners: List[Dict[str, Any]]
    hackathon_theme: Optional[str]
    hackathon_duration_days: int
    matches: List[PartnerMatch]
    team_composition: Optional[TeamComposition]


class HackathonPartnerAgent(BaseAgent):
    """
    AI Agent that finds compatible hackathon teammates.
    
    Considers:
    - Skill complementarity
    - Shared interests
    - Availability overlap
    - Timezone compatibility
    - Collaboration style
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.4,
    ):
        super().__init__(
            name="Hackathon Partner Agent",
            llm_model=llm_model,
            temperature=temperature,
        )
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.build_graph()
    
    def define_state(self) -> type:
        return HackathonPartnerState
    
    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        graph = StateGraph(HackathonPartnerState)
        
        # Add nodes
        graph.add_node("filter_by_availability", self.filter_by_availability)
        graph.add_node("calculate_compatibility", self.calculate_compatibility_scores)
        graph.add_node("rank_partners", self.rank_partners)
        graph.add_node("generate_team_composition", self.generate_team_composition)
        
        # Define edges
        graph.add_edge(START, "filter_by_availability")
        graph.add_edge("filter_by_availability", "calculate_compatibility")
        graph.add_edge("calculate_compatibility", "rank_partners")
        graph.add_edge("rank_partners", "generate_team_composition")
        graph.add_edge("generate_team_composition", END)
        
        self.graph = graph
        self.compiled_graph = graph.compile()
        return graph
    
    async def filter_by_availability(self, state: HackathonPartnerState) -> HackathonPartnerState:
        """Filter potential partners by availability."""
        user_profile = state.get("user_profile", {})
        user_availability = user_profile.get("availability", [])
        potential_partners = state.get("potential_partners", [])
        
        # Filter partners with overlapping availability
        filtered = []
        for partner in potential_partners:
            partner_avail = partner.get("availability", [])
            # Simple overlap check
            overlap = set(user_availability).intersection(set(partner_avail))
            if overlap or partner.get("flexible", False):
                partner["availability_overlap"] = list(overlap) or "flexible"
                filtered.append(partner)
        
        state["data"]["available_partners"] = filtered
        state["current_step"] = "availability_filtered"
        
        return state
    
    async def calculate_compatibility_scores(self, state: HackathonPartnerState) -> HackathonPartnerState:
        """Calculate compatibility scores for each potential partner."""
        user_profile = state.get("user_profile", {})
        user_skills = set(user_profile.get("skills", []))
        user_interests = set(user_profile.get("interests", []))
        
        available_partners = state.get("data", {}).get("available_partners", [])
        
        scored_partners = []
        for partner in available_partners:
            partner_skills = set(partner.get("skills", []))
            partner_interests = set(partner.get("interests", []))
            
            # Complementary skills (what they have that you don't)
            complementary = partner_skills - user_skills
            
            # Shared interests
            shared = user_interests.intersection(partner_interests)
            
            # Skill overlap (some overlap is good for communication)
            skill_overlap = user_skills.intersection(partner_skills)
            
            # Calculate scores
            complementary_score = len(complementary) / max(len(partner_skills), 1) * 0.4
            shared_interest_score = len(shared) / max(len(user_interests), 1) * 0.3
            overlap_score = min(len(skill_overlap) / 5, 1.0) * 0.2  # Cap at 5 overlapping skills
            
            # Timezone penalty
            tz_diff = abs(partner.get("timezone_offset", 0) - user_profile.get("timezone_offset", 0))
            tz_penalty = max(0, (tz_diff - 4) / 12) * 0.1  # Penalty if > 4 hours diff
            
            total_score = complementary_score + shared_interest_score + overlap_score - tz_penalty
            total_score = max(0, min(1, total_score))  # Clamp to [0, 1]
            
            # Determine compatibility level
            if total_score >= 0.85:
                level = CompatibilityLevel.PERFECT
            elif total_score >= 0.7:
                level = CompatibilityLevel.HIGH
            elif total_score >= 0.55:
                level = CompatibilityLevel.GOOD
            elif total_score >= 0.4:
                level = CompatibilityLevel.FAIR
            else:
                level = CompatibilityLevel.LOW
            
            scored_partners.append({
                **partner,
                "compatibility_score": total_score,
                "compatibility_level": level.value,
                "complementary_skills": list(complementary),
                "shared_interests": list(shared),
            })
        
        state["data"]["scored_partners"] = scored_partners
        state["current_step"] = "compatibility_calculated"
        
        return state
    
    async def rank_partners(self, state: HackathonPartnerState) -> HackathonPartnerState:
        """Rank partners and create match objects."""
        scored_partners = state.get("data", {}).get("scored_partners", [])
        
        # Sort by compatibility score
        scored_partners.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        matches = []
        for partner in scored_partners[:10]:  # Top 10 matches
            match = PartnerMatch(
                user_id=partner.get("user_id", ""),
                username=partner.get("username", ""),
                compatibility_score=partner.get("compatibility_score", 0),
                compatibility_level=CompatibilityLevel(partner.get("compatibility_level", "fair")),
                complementary_skills=partner.get("complementary_skills", []),
                shared_interests=partner.get("shared_interests", []),
                availability_overlap=partner.get("availability_overlap", "unknown"),
                timezone_diff_hours=abs(partner.get("timezone_offset", 0) - state.get("user_profile", {}).get("timezone_offset", 0)),
                previous_hackathons=partner.get("hackathon_count", 0),
                strengths=partner.get("strengths", []),
                collaboration_style=partner.get("collaboration_style", "unknown"),
            )
            matches.append(match)
        
        state["matches"] = matches
        state["current_step"] = "partners_ranked"
        
        return state
    
    async def generate_team_composition(self, state: HackathonPartnerState) -> HackathonPartnerState:
        """Generate recommended team composition."""
        user_profile = state.get("user_profile", {})
        matches = state.get("matches", [])
        hackathon_theme = state.get("hackathon_theme", "general")
        
        # Determine roles needed based on theme and user skills
        user_skills = set(user_profile.get("skills", []))
        
        typical_roles = ["frontend", "backend", "ml/ai", "design", "pitch/presentation"]
        
        # Identify skill gaps
        skill_gaps = []
        if "react" not in user_skills and "vue" not in user_skills and "angular" not in user_skills:
            skill_gaps.append("frontend_developer")
        if "python" not in user_skills and "node" not in user_skills and "go" not in user_skills:
            skill_gaps.append("backend_developer")
        if "machine-learning" not in user_skills and "tensorflow" not in user_skills:
            skill_gaps.append("ml_engineer")
        if "figma" not in user_skills and "design" not in user_skills:
            skill_gaps.append("designer")
        
        # Recommend partners to fill gaps
        recommended = []
        for match in matches[:4]:  # Up to 4 partners for team of 5
            recommended.append(match)
        
        team_comp = TeamComposition(
            ideal_size=min(5, 1 + len(recommended)),
            roles_needed=typical_roles,
            skill_gaps=skill_gaps,
            recommended_partners=recommended,
        )
        
        state["team_composition"] = team_comp
        state["result"] = {
            "matches": [m.model_dump() for m in matches],
            "team_composition": team_comp.model_dump(),
        }
        state["current_step"] = "complete"
        
        return state
    
    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Execute the hackathon partner matching workflow."""
        try:
            initial_state = self._initialize_state(input_data)
            initial_state["user_profile"] = input_data.get("user_profile", {})
            initial_state["potential_partners"] = input_data.get("potential_partners", [])
            initial_state["hackathon_theme"] = input_data.get("hackathon_theme")
            initial_state["hackathon_duration_days"] = input_data.get("duration_days", 3)
            initial_state["matches"] = []
            initial_state["team_composition"] = None
            
            if not self.compiled_graph:
                self.build_graph()
            
            result = await self.compiled_graph.ainvoke(initial_state)
            
            if result.get("errors"):
                return AgentResponse(
                    success=False,
                    errors=result["errors"],
                    message="Partner matching failed",
                )
            
            return AgentResponse(
                success=True,
                data=result.get("result", {}),
                message=f"Found {len(result.get('matches', []))} potential partners",
                metadata={
                    "partners_analyzed": len(result.get("potential_partners", [])),
                    "top_match_score": result["matches"][0].compatibility_score if result.get("matches") else 0,
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                errors=[str(e)],
                message="Partner matching failed",
            )
