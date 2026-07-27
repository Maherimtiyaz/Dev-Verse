"""
LangGraph Agent Architecture for DevVerse AI

This module defines the base agent structure and state management
for all AI agents in the platform.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from enum import Enum
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Available agent types in DevVerse AI."""
    GITHUB_ANALYZER = "github_analyzer"
    CODE_REVIEWER = "code_reviewer"
    MATCHMAKER = "matchmaker"
    CAREER_ADVISOR = "career_advisor"
    PROJECT_RECOMMENDER = "project_recommender"
    HACKATHON_PARTNER = "hackathon_partner"


class AgentState(TypedDict):
    """Base state structure for all agents."""
    messages: Annotated[List[BaseMessage], operator.add]
    context: Dict[str, Any]
    data: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    errors: List[str]
    current_step: str
    metadata: Dict[str, Any]


class AgentResponse(BaseModel):
    """Standardized response from any agent."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for all DevVerse AI agents.
    
    Each agent implements a LangGraph workflow with:
    - State management
    - Tool integration
    - Memory/context handling
    - Error handling
    """
    
    def __init__(
        self,
        name: str,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_iterations: int = 10,
    ):
        self.name = name
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.graph: Optional[StateGraph] = None
        self.compiled_graph = None
        self.tools: List[Any] = []
        
    @abstractmethod
    def define_state(self) -> type:
        """Define the state schema for this agent."""
        pass
    
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for this agent."""
        pass
    
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Execute the agent workflow."""
        pass
    
    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent's toolkit."""
        self.tools.append(tool)
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return f"You are {self.name}, an AI assistant for DevVerse AI platform."
    
    def _initialize_state(self, input_data: Dict[str, Any]) -> AgentState:
        """Initialize agent state from input data."""
        return AgentState(
            messages=[HumanMessage(content=str(input_data))],
            context=input_data.get("context", {}),
            data=input_data.get("data", {}),
            result=None,
            errors=[],
            current_step="initialization",
            metadata=input_data.get("metadata", {}),
        )
    
    def _handle_error(self, error: Exception, state: AgentState) -> AgentState:
        """Handle errors during agent execution."""
        state["errors"].append(str(error))
        state["current_step"] = "error"
        return state


class ToolResult(BaseModel):
    """Standardized tool execution result."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
