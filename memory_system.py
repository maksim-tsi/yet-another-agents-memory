# file: memory_system.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
import uuid
import redis
import json

# Import the facade for the persistent knowledge layer
from knowledge_store_manager import KnowledgeStoreManager

# --- Data Schemas for Operating Memory (Data Contracts) ---

class PersonalMemoryState(BaseModel):
    agent_id: str
    current_task_id: Optional[str] = None
    scratchpad: Dict[str, Any] = Field(default_factory=dict)
    promotion_candidates: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SharedWorkspaceState(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    status: Literal["active", "resolved", "cancelled"] = "active"
    shared_data: Dict[str, Any] = Field(default_factory=dict)
    participating_agents: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# --- Abstract Interface for the COMPLETE Memory System ---

class HybridMemorySystem(ABC):
    """
    Abstract base class defining the contract for the COMPLETE hybrid memory system.
    This is the SINGLE interface agents will use for all memory operations.
    """
    # --- Operating Memory Methods ---
    @abstractmethod
    def get_personal_state(self, agent_id: str) -> PersonalMemoryState:
        pass

    @abstractmethod
    def update_personal_state(self, state: PersonalMemoryState) -> None:
        pass

    @abstractmethod
    def get_shared_state(self, event_id: str) -> SharedWorkspaceState:
        pass

    @abstractmethod
    def update_shared_state(self, state: SharedWorkspaceState) -> None:
        pass
    
    @abstractmethod
    def publish_update(self, event_id: str, update_summary: Dict) -> None:
        pass

    # --- Persistent Knowledge Methods ---
    @abstractmethod
    def query_knowledge(
        self, 
        store_type: Literal["vector", "graph", "search"],
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Queries the persistent knowledge layer."""
        pass

# --- Concrete UNIFIED Implementation ---

class UnifiedMemorySystem(HybridMemorySystem):
    """
    A concrete implementation of the HybridMemorySystem, unifying Operating Memory (Redis)
    and the Persistent Knowledge Layer (via KnowledgeStoreManager).
    """
    
    def __init__(self, redis_client: redis.StrictRedis, knowledge_manager: KnowledgeStoreManager):
        """
        Initializes the memory system with clients for all layers.
        """
        # --- Operating Memory Client ---
        self.redis_client = redis_client
        try:
            if not self.redis_client.ping():
                raise ConnectionError("Could not connect to Redis.")
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            raise

        # --- Persistent Knowledge Layer Client ---
        self.knowledge_manager = knowledge_manager

    # --- Private Key Helpers for Redis ---
    def _get_personal_key(self, agent_id: str) -> str: return f"personal_state:{agent_id}"
    def _get_shared_key(self, event_id: str) -> str: return f"shared_state:{event_id}"
    def _get_channel_key(self, event_id: str) -> str: return f"channel:shared_state:{event_id}"

    # --- Operating Memory Implementation (Delegates to Redis) ---
    def get_personal_state(self, agent_id: str) -> PersonalMemoryState:
        key = self._get_personal_key(agent_id)
        raw_state = self.redis_client.get(key)
        if raw_state is None:
            return PersonalMemoryState(agent_id=agent_id)
        try:
            return PersonalMemoryState.model_validate_json(raw_state)
        except ValidationError as e:
            print(f"Data validation error for agent '{agent_id}': {e}")
            return PersonalMemoryState(agent_id=agent_id)

    def update_personal_state(self, state: PersonalMemoryState) -> None:
        key = self._get_personal_key(state.agent_id)
        state.last_updated = datetime.utcnow()
        self.redis_client.set(key, state.model_dump_json())

    def get_shared_state(self, event_id: str) -> SharedWorkspaceState:
        key = self._get_shared_key(event_id)
        raw_state = self.redis_client.get(key)
        if raw_state is None:
            raise KeyError(f"No shared workspace found for event_id: {event_id}")
        try:
            return SharedWorkspaceState.model_validate_json(raw_state)
        except ValidationError as e:
            raise ValueError(f"Corrupted data for event_id: {event_id}") from e

    def update_shared_state(self, state: SharedWorkspaceState) -> None:
        key = self._get_shared_key(state.event_id)
        state.last_updated = datetime.utcnow()
        self.redis_client.set(key, state.model_dump_json())
        update_summary = {
            "event_id": state.event_id, "status": state.status,
            "last_updated_by": state.participating_agents[-1] if state.participating_agents else "system"
        }
        self.publish_update(state.event_id, update_summary)

    def publish_update(self, event_id: str, update_summary: Dict) -> None:
        channel = self._get_channel_key(event_id)
        self.redis_client.publish(channel, json.dumps(update_summary))

    # --- Persistent Knowledge Implementation (Delegates to KnowledgeStoreManager) ---
    def query_knowledge(
        self, 
        store_type: Literal["vector", "graph", "search"],
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Delegates the query to the knowledge store manager."""
        return self.knowledge_manager.query(
            store_type=store_type,
            query_text=query_text,
            top_k=top_k,
            filters=filters
        )


if __name__ == '__main__':
    # --- Example Usage for the UNIFIED System ---
    
    # This setup requires all database services to be running.
    # We will use mock objects for a simple, self-contained demonstration.
    
    class MockQdrantStore:
        def query_similar(self, **kwargs): return [{"id": 1, "content": "Mock vector search result."}]
    class MockNeo4jStore:
        def query(self, **kwargs): return [{"node": "Mock graph query result."}]
    class MockMeilisearchStore:
        def search(self, **kwargs): return [{"title": "Mock text search result."}]
    
    print("--- Phase 3: Unified Memory System Demo ---")
    
    # 1. Instantiate all backend clients (using mocks for this demo)
    mock_qdrant = MockQdrantStore()
    mock_neo4j = MockNeo4jStore()
    mock_meili = MockMeilisearchStore()
    
    knowledge_manager = KnowledgeStoreManager(
        vector_store=mock_qdrant,
        graph_store=mock_neo4j,
        search_store=mock_meili
    )
    
    # Use an in-memory "fakeredis" for the demo to avoid a real connection
    import fakeredis
    fake_redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
    
    # 2. Instantiate the single, unified memory system
    memory = UnifiedMemorySystem(
        redis_client=fake_redis_client,
        knowledge_manager=knowledge_manager
    )
    print("UnifiedMemorySystem instantiated with mock backends.")

    # 3. Use Operating Memory (same as before)
    agent_id = "port_agent_007"
    print(f"\n--- Testing Operating Memory for agent: {agent_id} ---")
    personal_state = memory.get_personal_state(agent_id)
    personal_state.scratchpad["status"] = "monitoring"
    memory.update_personal_state(personal_state)
    retrieved_state = memory.get_personal_state(agent_id)
    print(f"Retrieved personal state from Redis: {retrieved_state.scratchpad['status']}")
    assert retrieved_state.scratchpad['status'] == 'monitoring'

    # 4. Use Persistent Knowledge Layer THROUGH THE SAME INTERFACE
    print("\n--- Testing Persistent Knowledge Layer ---")
    
    # An agent needs to find similar past events
    vector_results = memory.query_knowledge(
        store_type="vector",
        query_text="Find events about port congestion"
    )
    print(f"Vector search result: {vector_results}")
    assert vector_results[0]['content'] == "Mock vector search result."

    # An agent needs to find a specific relationship
    graph_results = memory.query_knowledge(
        store_type="graph",
        query_text="MATCH (v:Vessel)-[:HAS]->(c:Cargo) RETURN v, c"
    )
    print(f"Graph query result: {graph_results}")
    assert graph_results[0]['node'] == "Mock graph query result."

    # An agent needs to search operational manuals
    search_results = memory.query_knowledge(
        store_type="search",
        query_text="emergency crane protocol"
    )
    print(f"Text search result: {search_results}")
    assert search_results[0]['title'] == "Mock text search result."

    print("\n✅ Demo complete. The UnifiedMemorySystem successfully routes requests to both Operating and Persistent layers.")