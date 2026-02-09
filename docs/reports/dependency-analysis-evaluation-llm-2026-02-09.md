# Dependency Analysis: Evaluation & LLM Entry Points

**Date**: 2026-02-09  
**Analyst**: GitHub Copilot  
**Scope**: `src/evaluation/agent_wrapper.py`, `src/llm/`, shared modules

---

## Executive Summary

This analysis examines three architectural concerns raised during the codebase review. Key findings reveal **tight coupling** in the evaluation wrapper, **direct LLM imports** in both agents and memory subsystems, and the **absence of a shared commons module** despite its mention in specification documents.

---

## 1. Wrapper Coupling Analysis

**Question**: Does `agent_wrapper.py` import directly from `src/storage` or `src/memory/tiers`, or does it only use `UnifiedMemorySystem`?

### Finding: **TIGHT COUPLING CONFIRMED**

The evaluation wrapper bypasses the facade pattern and imports directly from lower-level modules:

```python
# src/evaluation/agent_wrapper.py - Lines 21-30
from memory_system import UnifiedMemorySystem          # ✅ Facade (root-level)
from src.agents.base_agent import BaseAgent
from src.agents.full_context_agent import FullContextAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.models import RunTurnRequest, RunTurnResponse
from src.agents.rag_agent import RAGAgent
from src.llm.client import LLMClient
from src.memory.models import TurnData
from src.memory.tiers import ActiveContextTier, WorkingMemoryTier      # ⚠️ Direct tier import
from src.storage.postgres_adapter import PostgresAdapter                 # ⚠️ Direct storage import
from src.storage.redis_adapter import RedisAdapter                       # ⚠️ Direct storage import
```

### Dependencies Breakdown

| Import Source | Module | Coupling Level |
|---------------|--------|----------------|
| Root | `UnifiedMemorySystem` | Facade ✅ |
| `src/agents` | `BaseAgent`, `MemoryAgent`, `RAGAgent`, `FullContextAgent` | Expected ✅ |
| `src/agents/models` | `RunTurnRequest`, `RunTurnResponse` | Expected ✅ |
| `src/llm` | `LLMClient` | **Direct** ⚠️ |
| `src/memory/models` | `TurnData` | Data model ✅ |
| `src/memory/tiers` | `ActiveContextTier`, `WorkingMemoryTier` | **Direct** ⚠️ |
| `src/storage` | `PostgresAdapter`, `RedisAdapter` | **Direct** ⚠️ |

### Justification in Code

The wrapper performs manual tier initialization (lines 192-232) rather than using `UnifiedMemorySystem` exclusively:

```python
# Line 201-223: Direct adapter instantiation
redis_adapter = RedisAdapter({...})
postgres_l1 = PostgresAdapter({"url": config.postgres_url, "table": "active_context"})
postgres_l2 = PostgresAdapter({"url": config.postgres_url, "table": "working_memory", ...})

l1_tier = ActiveContextTier(redis_adapter=redis_adapter, postgres_adapter=postgres_l1, ...)
l2_tier = WorkingMemoryTier(postgres_adapter=postgres_l2, ...)
```

### Architectural Implication

The wrapper duplicates UnifiedMemorySystem's initialization logic. This creates:
- **Drift risk**: Changes to tier configuration in `src/memory/system.py` won't propagate to wrapper
- **Test brittleness**: Integration tests must mock at multiple levels
- **Violation**: ADR-003 principle of tier abstraction

---

## 2. The LLM Triangle Analysis

**Question**: Does `src/agents` import `src/llm` directly, or does it rely on the Memory System to pass the LLM client?

### Finding: **DIRECT IMPORT BY BOTH**

Both `src/agents` and `src/memory` import `LLMClient` directly. The memory system does NOT act as an intermediary.

### Agent Layer Imports

| Agent | Import |
|-------|--------|
| `full_context_agent.py:10` | `from src.llm.client import LLMClient` |
| `rag_agent.py:11` | `from src.llm.client import LLMClient` |
| `memory_agent.py:16` | `from src.llm.client import LLMClient` |

### Memory Layer Imports

| Engine/Module | Import |
|---------------|--------|
| `src/memory/system.py:12` | `from src.llm.client import LLMClient` |
| `src/memory/engines/fact_extractor.py:17` | `from src.llm.client import LLMClient` |
| `src/memory/engines/topic_segmenter.py:16` | `from src.llm.client import LLMClient` |
| `src/memory/engines/consolidation_engine.py:24-25` | `from src.llm.client import LLMClient` and `BaseProvider` |

### Dependency Pattern

```
                    src/llm
                      │
          ┌───────────┴───────────┐
          │                       │
      src/agents              src/memory
          │                       │
          └───────────┬───────────┘
                      │
            src/evaluation
```

### Architectural Implication

- **No centralized LLM management**: Each subsystem instantiates its own `LLMClient`
- **Opportunity**: `UnifiedMemorySystem` could pass its `LLMClient` to agents, but currently agents receive it directly at construction
- **Phoenix Instrumentation**: Located in `src/llm/client.py` (lines 32-100), auto-initializes at module import time

---

## 3. Shared Commons Analysis

**Question**: Does `src/common` (e.g., `telemetry.py`) exist and is it imported by both `src/memory` and `src/agents`?

### Finding: **NO `src/common` DIRECTORY EXISTS**

The `src/common/` directory does not exist in the current codebase.

```bash
$ ls src/
__init__.py  agents/  evaluation/  llm/  memory/  storage/  utils/
```

### Telemetry Implementation

Telemetry is currently implemented via **two separate mechanisms**, neither in a shared module:

#### A. Memory Tier Telemetry (Parameter Injection)

`BaseTier` accepts an optional `telemetry_stream` parameter:

```python
# src/memory/tiers/base_tier.py:72-76
def __init__(
    self,
    storage_adapters: Mapping[str, StorageAdapter],
    metrics_collector: MetricsCollector | None = None,
    config: dict[str, Any] | None = None,
    telemetry_stream: Any | None = None,  # ← Glass Box observability
):
```

Used by: `EpisodicMemoryTier`, `SemanticMemoryTier`, `ActiveContextTier`, `WorkingMemoryTier`

#### B. LLM Client Telemetry (Phoenix/OpenTelemetry)

`src/llm/client.py` has built-in Phoenix instrumentation:

```python
# src/llm/client.py:32-100
def _init_phoenix_instrumentation() -> None:
    """Initialize Phoenix/OpenTelemetry instrumentation if configured."""
    endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT")
    # ...
    from opentelemetry import trace
    from phoenix.otel import register
    # ...
```

### Spec Document Reference

The specification document mentions a future `src/common/telemetry` module:

```python
# docs/specs/spec-concept2-mas-memory-inspector-prerequisites.md:134
from src.common.telemetry import telemetry, CognitiveEvent
```

**This module has not been implemented.**

### Cross-Module Sharing

Currently, NO module is imported by both `src/agents` and `src/memory`:

| Shared Dependency | Agents | Memory |
|-------------------|--------|--------|
| `src/llm.client.LLMClient` | ✓ | ✓ |
| `src/memory/models` | ✓ (ContextBlock, TurnData) | ✓ |
| `src/storage/*` | ✗ | ✓ |
| `src/common/*` | N/A | N/A |

---

## 4. Circular Dependency Alert

One circular import pattern was identified:

```
src/storage/redis_adapter.py:43 → from src/memory/namespace import NamespaceManager
src/memory/tiers/*                → from src/storage/*
```

- **Impact**: Currently benign (namespace is import-time safe)
- **Risk**: Future changes to `NamespaceManager` could cause import loops

---

## Recommendations

### 1. Wrapper Refactoring (High Priority)

Modify `agent_wrapper.py` to use `UnifiedMemorySystem` for all tier/adapter operations:

```python
# Proposed: Use factory method on UnifiedMemorySystem
memory = UnifiedMemorySystem.from_config(config)
agent = agent_cls(llm_client=llm_client, memory_system=memory)
```

### 2. LLM Client Injection (Medium Priority)

Consider passing `LLMClient` through `UnifiedMemorySystem` to reduce direct imports:

```python
# Current (direct)
agent = MemoryAgent(llm_client=LLMClient.from_env(), memory_system=mem)

# Proposed (injected from memory system)
agent = MemoryAgent(memory_system=mem)  # mem.llm_client used internally
```

### 3. Shared Commons Module (Low Priority)

Create `src/common/telemetry.py` to unify telemetry patterns:

```python
# Proposed: src/common/telemetry.py
class CognitiveEvent(TypedDict):
    event_type: str
    timestamp: datetime
    tier: str
    metadata: dict

def emit_event(event: CognitiveEvent) -> None:
    """Unified emission to both Phoenix and LifecycleStream."""
    ...
```

---

## Dependency Graph

```
                         ┌────────────────┐
                         │  agent_wrapper │
                         └───────┬────────┘
                 ┌───────────────┼───────────────┐
                 │               │               │
         ┌───────▼───────┐ ┌─────▼─────┐ ┌───────▼───────┐
         │  src/agents   │ │  src/llm  │ │ src/storage   │
         └───────┬───────┘ └─────┬─────┘ └───────┬───────┘
                 │               │               │
                 │    ┌──────────┘               │
                 │    │                          │
         ┌───────▼────▼────┐             ┌───────▼────────┐
         │   src/memory    │◄────────────│ memory/tiers   │
         │    (system)     │             │ (use storage)  │
         └─────────────────┘             └────────────────┘
```

---

## Files Analyzed

| File | Purpose |
|------|---------|
| [src/evaluation/agent_wrapper.py](src/evaluation/agent_wrapper.py) | FastAPI benchmark wrapper |
| [src/llm/client.py](src/llm/client.py) | Multi-provider LLM orchestrator |
| [src/memory/system.py](src/memory/system.py) | Unified memory facade |
| [memory_system.py](memory_system.py) | Root-level memory facade (legacy) |
| [src/memory/tiers/base_tier.py](src/memory/tiers/base_tier.py) | Abstract tier interface |
| [src/memory/namespace.py](src/memory/namespace.py) | Redis key generation |

---

*Report generated by GitHub Copilot Agent*
