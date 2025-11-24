"""Base Agent class for all research agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Represents the state of an agent execution."""
    
    agent_name: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all agents in the research system."""
    
    def __init__(self, name: str, llm_client=None, model_name: str = None):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent
            llm_client: LLM client instance (OpenAI, Anthropic, etc.)
            model_name: Name of the model to use (e.g., 'llama-3.1-70b-versatile')
        """
        self.name = name
        self.llm_client = llm_client
        self.model_name = model_name
        self.logger = logging.getLogger(f"Agent.{name}")
        self.state = AgentState(agent_name=name)
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary task.
        
        Args:
            input_data: Input parameters for the agent
            
        Returns:
            Dictionary containing the agent's output
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> AgentState:
        """
        Run the agent with error handling and state management.
        
        Args:
            input_data: Input parameters for the agent
            
        Returns:
            AgentState object with execution results
        """
        self.state.status = "running"
        self.state.start_time = datetime.now()
        self.state.input_data = input_data
        
        try:
            self.logger.info(f"Starting {self.name}")
            output = await self.execute(input_data)
            
            self.state.output_data = output
            self.state.status = "completed"
            self.logger.info(f"Completed {self.name}")
            
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {str(e)}", exc_info=True)
            self.state.status = "failed"
            self.state.errors.append(str(e))
            
        finally:
            self.state.end_time = datetime.now()
            
        return self.state
    
    def validate_input(self, input_data: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate that required input keys are present.
        
        Args:
            input_data: Input dictionary to validate
            required_keys: List of required keys
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        missing_keys = [key for key in required_keys if key not in input_data]
        if missing_keys:
            raise ValueError(f"Missing required input keys: {missing_keys}")
        return True
    
    def log_progress(self, message: str, level: str = "info"):
        """Log progress message."""
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[{self.name}] {message}")


class AgentMessage(BaseModel):
    """Message passed between agents."""
    
    from_agent: str
    to_agent: str
    timestamp: datetime = Field(default_factory=datetime.now)
    content: Dict[str, Any]
    message_type: str = "data"  # data, request, response, error
    priority: int = 1  # 1=low, 5=high
