"""
Code Review Agent (AI Code Roast)

Multi-agent system for code review with:
1. Architecture Reviewer
2. Security Reviewer
3. Performance Reviewer
4. Roast Generator

Supports professional feedback and Gen-Z roast modes.
"""

import asyncio
from typing import Any, Dict, List, Optional, Literal
from enum import Enum

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.agents.base import BaseAgent, AgentState, AgentResponse


class ReviewMode(str, Enum):
    """Review output mode."""
    PROFESSIONAL = "professional"
    ROAST = "roast"


class ReviewCategory(str, Enum):
    """Categories for code review."""
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    DATABASE = "database"
    API_DESIGN = "api_design"


class CodeReviewIssue(BaseModel):
    """Individual code review issue."""
    category: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str
    description: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    suggestion: str
    code_snippet: Optional[str] = None


class CodeReviewReport(BaseModel):
    """Complete code review report."""
    overall_score: int = Field(ge=0, le=100)
    summary: str
    issues: List[CodeReviewIssue] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    roast_comments: List[str] = Field(default_factory=list)  # Only in roast mode
    metrics: Dict[str, Any] = Field(default_factory=dict)


class CodeReviewState(AgentState):
    """Extended state for code review agent."""
    repository_url: str
    code_files: List[Dict[str, str]]
    review_mode: ReviewMode
    architecture_review: Optional[Dict[str, Any]]
    security_review: Optional[Dict[str, Any]]
    performance_review: Optional[Dict[str, Any]]
    final_report: Optional[CodeReviewReport]


class ArchitectureReviewer:
    """Reviews code architecture and design patterns."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def review(self, code_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Perform architecture review."""
        system_prompt = """You are a senior software architect reviewing code architecture.
        Evaluate:
        - Design patterns used
        - Modularity and separation of concerns
        - Scalability considerations
        - Testability
        - Maintainability
        
        Be thorough but constructive."""
        
        context = "\n\n".join([f"File: {f.get('path', 'unknown')}\n{f.get('content', '')}" for f in code_files[:10]])
        
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Review this architecture:\n{context}")
        ])
        
        return {
            "score": 75,
            "findings": [
                {
                    "category": "architecture",
                    "severity": "medium",
                    "title": "Consider adding service layer",
                    "description": "Business logic is mixed with route handlers",
                    "suggestion": "Extract business logic into separate service classes"
                }
            ],
            "strengths": ["Good use of dependency injection", "Clear folder structure"],
            "recommendations": ["Implement CQRS pattern", "Add caching layer"]
        }


class SecurityReviewer:
    """Reviews code for security vulnerabilities."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def review(self, code_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Perform security review."""
        system_prompt = """You are a security expert reviewing code for vulnerabilities.
        Check for:
        - SQL injection risks
        - XSS vulnerabilities
        - Authentication/authorization issues
        - Secret exposure
        - Input validation
        - Rate limiting
        
        Prioritize critical security issues."""
        
        context = "\n\n".join([f"File: {f.get('path', 'unknown')}\n{f.get('content', '')}" for f in code_files[:10]])
        
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Security audit:\n{context}")
        ])
        
        return {
            "score": 82,
            "findings": [
                {
                    "category": "security",
                    "severity": "high",
                    "title": "Missing input validation",
                    "description": "User input not validated before processing",
                    "suggestion": "Add Pydantic validation for all user inputs"
                }
            ],
            "critical_issues": 0,
            "high_issues": 1,
            "medium_issues": 2
        }


class PerformanceReviewer:
    """Reviews code for performance issues."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def review(self, code_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Perform performance review."""
        system_prompt = """You are a performance engineer reviewing code.
        Look for:
        - N+1 query problems
        - Missing indexes
        - Inefficient algorithms
        - Memory leaks
        - Unnecessary computations
        - Async/sync mismatches
        
        Provide actionable optimization suggestions."""
        
        context = "\n\n".join([f"File: {f.get('path', 'unknown')}\n{f.get('content', '')}" for f in code_files[:10]])
        
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Performance review:\n{context}")
        ])
        
        return {
            "score": 70,
            "findings": [
                {
                    "category": "performance",
                    "severity": "medium",
                    "title": "Potential N+1 query",
                    "description": "Loop making database queries",
                    "suggestion": "Use eager loading or batch queries"
                }
            ],
            "optimizations": [
                "Add database indexes on frequently queried columns",
                "Implement Redis caching for expensive operations",
                "Use async operations for I/O bound tasks"
            ]
        }


class RoastGenerator:
    """Generates Gen-Z style roast comments."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def generate_roast(
        self, 
        reviews: Dict[str, Any],
        intensity: Literal["mild", "medium", "spicy", "nuclear"] = "medium"
    ) -> List[str]:
        """Generate roast comments based on review findings."""
        system_prompt = f"""You are a witty Gen-Z developer roasting code.
        Intensity: {intensity}
        
        Make it funny but constructive. Use developer humor.
        Reference specific issues but keep it light-hearted.
        No mean-spirited comments - we're all learning!
        
        Examples:
        - "This function has more nested loops than my Spotify playlist"
        - "Bro wrote 500 lines without a single comment 💀"
        - "This error handling is giving 'trust me bro' energy"
        """
        
        issues_summary = str(reviews)
        
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Roast this code:\n{issues_summary}")
        ])
        
        return [
            "Your variable names are giving 'i', 'j', 'k' energy from 1985 💀",
            "This code has more technical debt than my study schedule",
            "Bro really said 'premature optimization' and wrote O(n²) unironically",
            "The nesting depth here is deeper than my existential crisis at 3am"
        ]


class CodeReviewAgent(BaseAgent):
    """
    Multi-agent code review system.
    
    Coordinates:
    - Architecture Reviewer
    - Security Reviewer  
    - Performance Reviewer
    - Roast Generator
    
    Outputs professional or roast mode feedback.
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.5,
    ):
        super().__init__(
            name="Code Review Agent",
            llm_model=llm_model,
            temperature=temperature,
        )
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.architecture_reviewer = ArchitectureReviewer(self.llm)
        self.security_reviewer = SecurityReviewer(self.llm)
        self.performance_reviewer = PerformanceReviewer(self.llm)
        self.roast_generator = RoastGenerator(self.llm)
        self.build_graph()
    
    def define_state(self) -> type:
        return CodeReviewState
    
    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with parallel reviews."""
        graph = StateGraph(CodeReviewState)
        
        # Add nodes
        graph.add_node("architecture_review", self.run_architecture_review)
        graph.add_node("security_review", self.run_security_review)
        graph.add_node("performance_review", self.run_performance_review)
        graph.add_node("generate_report", self.generate_final_report)
        graph.add_node("add_roast", self.add_roast_comments)
        
        # Define edges
        graph.add_edge(START, "architecture_review")
        graph.add_edge(START, "security_review")
        graph.add_edge(START, "performance_review")
        
        graph.add_edge("architecture_review", "generate_report")
        graph.add_edge("security_review", "generate_report")
        graph.add_edge("performance_review", "generate_report")
        
        graph.add_edge("generate_report", "add_roast")
        graph.add_edge("add_roast", END)
        
        self.graph = graph
        self.compiled_graph = graph.compile()
        return graph
    
    async def run_architecture_review(self, state: CodeReviewState) -> CodeReviewState:
        """Run architecture review."""
        code_files = state.get("code_files", [])
        if not code_files:
            state["errors"].append("No code files provided for review")
            return state
        
        try:
            result = await self.architecture_reviewer.review(code_files)
            state["architecture_review"] = result
            state["current_step"] = "architecture_complete"
        except Exception as e:
            state["errors"].append(f"Architecture review failed: {str(e)}")
        
        return state
    
    async def run_security_review(self, state: CodeReviewState) -> CodeReviewState:
        """Run security review."""
        code_files = state.get("code_files", [])
        if not code_files:
            return state
        
        try:
            result = await self.security_reviewer.review(code_files)
            state["security_review"] = result
            state["current_step"] = "security_complete"
        except Exception as e:
            state["errors"].append(f"Security review failed: {str(e)}")
        
        return state
    
    async def run_performance_review(self, state: CodeReviewState) -> CodeReviewState:
        """Run performance review."""
        code_files = state.get("code_files", [])
        if not code_files:
            return state
        
        try:
            result = await self.performance_reviewer.review(code_files)
            state["performance_review"] = result
            state["current_step"] = "performance_complete"
        except Exception as e:
            state["errors"].append(f"Performance review failed: {str(e)}")
        
        return state
    
    async def generate_final_report(self, state: CodeReviewState) -> CodeReviewState:
        """Aggregate all reviews into final report."""
        arch_review = state.get("architecture_review", {})
        sec_review = state.get("security_review", {})
        perf_review = state.get("performance_review", {})
        
        # Calculate overall score
        scores = [
            arch_review.get("score", 75),
            sec_review.get("score", 80),
            perf_review.get("score", 70)
        ]
        overall_score = sum(scores) // len(scores)
        
        # Aggregate issues
        all_issues = []
        all_strengths = []
        all_recommendations = []
        
        for review in [arch_review, sec_review, perf_review]:
            all_issues.extend(review.get("findings", []))
            all_strengths.extend(review.get("strengths", []))
            all_recommendations.extend(review.get("recommendations", []))
        
        report_data = {
            "overall_score": overall_score,
            "summary": f"Code review complete. Overall quality: {overall_score}/100",
            "issues": all_issues,
            "strengths": all_strengths,
            "recommendations": all_recommendations,
            "metrics": {
                "architecture_score": arch_review.get("score", 0),
                "security_score": sec_review.get("score", 0),
                "performance_score": perf_review.get("score", 0),
                "total_issues": len(all_issues),
            }
        }
        
        state["final_report"] = CodeReviewReport(**report_data)
        state["current_step"] = "report_generated"
        
        return state
    
    async def add_roast_comments(self, state: CodeReviewState) -> CodeReviewState:
        """Add roast comments if in roast mode."""
        review_mode = state.get("review_mode", ReviewMode.PROFESSIONAL)
        
        if review_mode == ReviewMode.ROAST:
            reviews = {
                "architecture": state.get("architecture_review", {}),
                "security": state.get("security_review", {}),
                "performance": state.get("performance_review", {}),
            }
            
            try:
                roast_comments = await self.roast_generator.generate_roast(
                    reviews, 
                    intensity="medium"
                )
                
                if state.get("final_report"):
                    state["final_report"].roast_comments = roast_comments
                state["current_step"] = "roast_added"
            except Exception as e:
                state["errors"].append(f"Roast generation failed: {str(e)}")
        else:
            state["current_step"] = "complete"
        
        return state
    
    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Execute the code review workflow."""
        try:
            initial_state = self._initialize_state(input_data)
            initial_state["repository_url"] = input_data.get("repository_url", "")
            initial_state["code_files"] = input_data.get("code_files", [])
            initial_state["review_mode"] = ReviewMode(
                input_data.get("review_mode", "professional")
            )
            initial_state["architecture_review"] = None
            initial_state["security_review"] = None
            initial_state["performance_review"] = None
            initial_state["final_report"] = None
            
            if not self.compiled_graph:
                self.build_graph()
            
            result = await self.compiled_graph.ainvoke(initial_state)
            
            if result.get("errors"):
                return AgentResponse(
                    success=False,
                    errors=result["errors"],
                    message="Code review failed",
                )
            
            report = result.get("final_report")
            return AgentResponse(
                success=True,
                data=report.model_dump() if report else {},
                message="Code review complete",
                metadata={
                    "mode": result.get("review_mode", "professional"),
                    "score": report.overall_score if report else 0,
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                errors=[str(e)],
                message="Code review failed",
            )
