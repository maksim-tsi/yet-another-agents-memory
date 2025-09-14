# file: memory_system.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- Data Schemas for Operating Memory ---

class PersonalMemoryState(BaseModel):
    """
    Schema for an agent's private scratchpad, stored as a Redis Hash.
    """
    agent_id: str
    current_task_id: Optional[str] = None
    # Intermediate thoughts, calculations, or API results
    scratchpad: Dict[str, Any] = Field(default_factory=dict)
    # Data being evaluated for promotion (CIAR model)
    promotion_candidates: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SharedWorkspaceState(BaseModel):
    """
    Schema for the shared workspace, representing a collaborative event.
    Stored as a Redis Hash.
    """
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    status: Literal["active", "resolved", "cancelled"] = "active"
    # The core, shared facts and state data for the event
    shared_data: Dict[str, Any] = Field(default_factory=dict)
    # Log of agents who have contributed to this event
    participating_agents: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# --- Abstract Interface for the Memory System ---

class HybridMemorySystem(ABC):
    """
    Abstract base class defining the contract for our hybrid memory system.
    Agents will interact with this interface, not the raw Redis client.
    """

    @abstractmethod
    def get_personal_state(self, agent_id: str) -> PersonalMemoryState:
        """Retrieves the full personal state for a given agent."""
        pass

    @abstractmethod
    def update_personal_state(self, agent_id: str, state: PersonalMemoryState) -> None:
        """Overwrites the personal state for a given agent."""
        pass

    @abstractmethod
    def get_shared_state(self, event_id: str) -> SharedWorkspaceState:
        """Retrieves the full state of a shared event."""
        pass

    @abstractmethod
    def update_shared_state(self, event_id: str, state: SharedWorkspaceState) -> None:
        """Overwrites the state of a shared event."""
        pass
    
    @abstractmethod
    def publish_update(self, event_id: str, update_summary: Dict) -> None:
        """Publishes a notification that a shared event has been updated."""
        pass

    # ... Other methods for querying persistent knowledge would go here ...