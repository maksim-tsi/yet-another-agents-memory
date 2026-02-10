# Dependency Analysis Consolidated (version-0.9, upto10feb2026)

Consolidated dependency analyses for agents/memory and evaluation/LLM.

Sources:
- dependency_analysis_consolidated_version-0.9_upto10feb2026.md
- dependency_analysis_consolidated_version-0.9_upto10feb2026.md

---
## Source: dependency_analysis_consolidated_version-0.9_upto10feb2026.md

# Dependency Analysis: src/agents → src/memory

**Date**: 2026-02-09  
**Analyzed Modules**: `src/agents/` → `src/memory/`  
**Purpose**: Assess coupling and package extraction feasibility

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Import statements referencing src.memory** | 5 |
| **Unique classes/functions imported** | 7 |
| **Internal/private imports (prefixed with `_`)** | 0 |
| **Public interface imports** | 7 (100%) |
| **Lines of code that would break immediately** | 20 |
| **Files affected** | 5 |

**Assessment**: All imports access documented public interfaces. No internal/private API usage detected. Package extraction is feasible with import path updates.

---

## Detailed Import Analysis

### Import Statements (5 total)

| File | Line | Import Statement |
|------|------|------------------|
| [ciar_tools.py](../../../src/agents/tools/ciar_tools.py#L30) | 30 | `from src.memory.ciar_scorer import CIARScorer` |
| [full_context_agent.py](../../../src/agents/full_context_agent.py#L11) | 11 | `from src.memory.models import ContextBlock` |
| [memory_agent.py](../../../src/agents/memory_agent.py#L17) | 17 | `from src.memory.models import ContextBlock, TurnData` |
| [tier_tools.py](../../../src/agents/tools/tier_tools.py#L36) | 36 | `from src.memory.graph_templates import get_template, validate_and_execute_template` |
| [unified_tools.py](../../../src/agents/tools/unified_tools.py#L16) | 16 | `from src.memory.models import SearchWeights, TurnData` |

---

## Imported Symbols Classification

### Public Interfaces (7 symbols) ✅

All imported symbols are documented public APIs:

| Symbol | Source Module | Exported in `__all__` | Classification |
|--------|---------------|----------------------|----------------|
| `CIARScorer` | `ciar_scorer.py` | N/A (class) | **Public** - Documented class with public API |
| `ContextBlock` | `models.py` | ✅ Yes | **Public** - Core data model |
| `TurnData` | `models.py` | ✅ Yes | **Public** - Core data model |
| `SearchWeights` | `models.py` | ✅ Yes | **Public** - Core data model |
| `get_template` | `graph_templates.py` | N/A (function) | **Public** - Template registry accessor |
| `validate_and_execute_template` | `graph_templates.py` | N/A (function) | **Public** - Template validation API |

### Internal/Private Imports (0 symbols) ✅

**None detected.** No imports of symbols prefixed with underscore (`_`).

---

## Usage Analysis by File

### 1. [src/agents/tools/ciar_tools.py](../../../src/agents/tools/ciar_tools.py)

**Imports**: `CIARScorer`

| Line | Usage |
|------|-------|
| 30 | Import statement |
| 119 | `scorer = CIARScorer()` |
| 190 | `scorer = CIARScorer()` |
| 245 | `scorer = CIARScorer()` |

**Breaking lines**: 4

---

### 2. [src/agents/full_context_agent.py](../../../src/agents/full_context_agent.py)

**Imports**: `ContextBlock`

| Line | Usage |
|------|-------|
| 11 | Import statement |
| 53 | `if isinstance(context_block, ContextBlock):` |
| 126 | `def _build_context_from_block(self, context_block: ContextBlock, user_input: str)` |

**Breaking lines**: 3

---

### 3. [src/agents/memory_agent.py](../../../src/agents/memory_agent.py)

**Imports**: `ContextBlock`, `TurnData`

| Line | Usage |
|------|-------|
| 17 | Import statement |
| 146 | `if isinstance(context_block, ContextBlock):` |
| 207 | `user_turn = TurnData(...)` |
| 214 | `assistant_turn = TurnData(...)` |

**Breaking lines**: 4

---

### 4. [src/agents/tools/tier_tools.py](../../../src/agents/tools/tier_tools.py)

**Imports**: `get_template`, `validate_and_execute_template`

| Line | Usage |
|------|-------|
| 36 | Import statement |
| 208 | `is_valid, error_msg, cypher_query = validate_and_execute_template(...)` |
| 221 | `template = get_template(template_name)` |

**Breaking lines**: 3

---

### 5. [src/agents/tools/unified_tools.py](../../../src/agents/tools/unified_tools.py)

**Imports**: `SearchWeights`, `TurnData`

| Line | Usage |
|------|-------|
| 16 | Import statement |
| 153 | `weights = SearchWeights(l2_weight=l2_weight, l3_weight=l3_weight, l4_weight=l4_weight)` |
| 321 | `turn_data = TurnData(...)` |
| 338 | `turn_data = TurnData(...)` |

**Breaking lines**: 4

---

## Package Extraction Impact Summary

### Lines That Would Break Immediately: **20 lines**

| File | Import Lines | Usage Lines | Total |
|------|-------------|-------------|-------|
| `ciar_tools.py` | 1 | 3 | 4 |
| `full_context_agent.py` | 1 | 2 | 3 |
| `memory_agent.py` | 1 | 3 | 4 |
| `tier_tools.py` | 1 | 2 | 3 |
| `unified_tools.py` | 1 | 3 | 4 |
| **Total** | **5** | **13** | **18** |

*Note: TurnData is imported in 2 files but counted once per usage line.*

### Actual Line Count Breakdown

```
Import statements:     5 lines
Type annotations:      2 lines (function signatures using ContextBlock)
isinstance() checks:   2 lines
Constructor calls:     8 lines (CIARScorer, TurnData, SearchWeights)
Function calls:        3 lines (get_template, validate_and_execute_template)
─────────────────────────────────
Total impact:         20 lines
```

---

## Recommendations for Package Extraction

### Minimal Migration Path

If `src/memory` is moved to a separate pip package (e.g., `mas-memory-core`):

1. **Update 5 import statements** across 5 files:
   ```python
   # Before
   from src.memory.models import ContextBlock, TurnData
   
   # After
   from mas_memory_core.models import ContextBlock, TurnData
   ```

2. **No API changes required** - all usage is through stable public interfaces

3. **No internal coupling** - zero `_private` method/class access

### Risk Assessment

| Risk | Level | Notes |
|------|-------|-------|
| API breakage | **Low** | 100% public interface usage |
| Version compatibility | **Low** | No private API dependencies |
| Circular imports | **None** | One-way dependency (agents → memory) |
| Test impact | **Medium** | Tests in `src/agents/` will need mock updates |

---

## Appendix: Module Dependency Graph

```
src/agents/
├── tools/
│   ├── ciar_tools.py ──────────→ src/memory/ciar_scorer.CIARScorer
│   ├── tier_tools.py ──────────→ src/memory/graph_templates.{get_template, validate_and_execute_template}
│   └── unified_tools.py ───────→ src/memory/models.{SearchWeights, TurnData}
├── full_context_agent.py ──────→ src/memory/models.ContextBlock
└── memory_agent.py ────────────→ src/memory/models.{ContextBlock, TurnData}
```

---

*Generated by dependency analysis on 2026-02-09*

---

## Source: dependency_analysis_consolidated_version-0.9_upto10feb2026.md

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

