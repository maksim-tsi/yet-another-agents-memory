# Phase 2E: Generic BaseTier Refactoring — Implementation Guide

**Version:** 2.0 (Updated 2026-02-04)  
**Status:** In Progress (~85% Complete)  
**Estimated Remaining Effort:** 4-8 hours  

---

## Executive Summary

This document guides the completion of Phase 2E: converting the memory tier system to use
fully type-safe generic interfaces. The refactoring ensures **compile-time type safety**
via mypy, **API symmetry** between `store()` and `retrieve()`, and alignment with the
**"Reasoning-First" schema pattern** from our research.

### Current State (as of 2026-02-04)

| Component | Status | Notes |
|-----------|--------|-------|
| `BaseTier[TModel]` generic definition | ✅ Complete | Uses Python 3.12+ `class BaseTier[TModel: BaseModel]` |
| `TurnData` model for L1 | ✅ Complete | Exists in `models.py` with all fields |
| All tiers use generics | ✅ Complete | L1=`TurnData`, L2=`Fact`, L3=`Episode`, L4=`KnowledgeDocument` |
| `retrieve()` returns typed `T` | ✅ Complete | All tiers return model instances |
| `query()` returns `list[T]` | ✅ Complete | All tiers return typed lists |
| `store()` accepts `TModel` | ⚠️ **INCOMPLETE** | Still declares `dict[str, Any]` |
| Engine callers updated | ⚠️ **INCOMPLETE** | Engines call `.model_dump()` before storing |
| Test type assertions | ⚠️ **INCOMPLETE** | Need `isinstance()` checks |

### Remaining Work

1. **Update `store()` signature** to accept `TModel | dict[str, Any]` with deprecation
2. **Migrate engine callers** to pass models directly instead of `.model_dump()`
3. **Add type safety assertions** to tests
4. **Handle L3 special case** with `EpisodeStoreInput` model
5. **Run mypy strict checks** and resolve all errors

---

## Research Foundation

This plan is based on two research reports:

- [`refactoring_memory_tiers_research_analysis.md`](../research/refactoring_memory_tiers_research_analysis.md)
- [`refactoring_memory_tiers_2_type_safe.md`](../research/refactoring_memory_tiers_2_type_safe.md)

### Key Research Findings

| Finding | Recommendation | Source |
|---------|---------------|--------|
| "Stringly typed" bottleneck | Eliminate `dict[str, Any]` at tier boundaries | Section 1.3 |
| Silent failures from dict keys | Use Pydantic models for compile-time checks | Section 1.3 |
| Generic signature | `store(data: T) -> str` and `retrieve(str) -> T` | Section 3.1 |
| L1 model gap | Create `TurnData(BaseModel)` | Section 5.1 |
| Rollout order | Bottom-up: L4 → L3 → L2 → L1 | Section 5.2 |
| Performance | Pydantic v2 validation <0.1ms; negligible | Table 2 |

---

## Implementation Phases

### Phase 2E.1: Update `store()` Signature ⬅️ **START HERE**

**Goal:** Change `store()` to accept typed models while maintaining backward compatibility.

#### Step 1: Update `BaseTier.store()` Abstract Method

**File:** `src/memory/tiers/base_tier.py`

**Current (line ~105):**
```python
@abstractmethod
async def store(self, data: dict[str, Any]) -> str:
```

**Target:**
```python
@abstractmethod
async def store(self, data: TModel | dict[str, Any]) -> str:
    """
    Store data in this tier.

    Args:
        data: Pydantic model instance or dict (deprecated).
            Passing dict is deprecated and will emit a warning.
            Use the tier's model type directly:
            - L1: TurnData
            - L2: Fact
            - L3: Episode (or EpisodeStoreInput for full payload)
            - L4: KnowledgeDocument

    Returns:
        Unique identifier for stored data

    Raises:
        TierOperationError: If storage operation fails
        ValidationError: If dict data fails model validation
    """
    pass
```

**Mypy Considerations:**
- `TModel` is a type parameter, so `TModel | dict[str, Any]` works correctly
- Each concrete tier will have specific union: `Fact | dict[str, Any]`, etc.
- Use `isinstance(data, dict)` for runtime dispatch

#### Step 2: Update Each Tier's `store()` Implementation

Apply this pattern to all 4 tiers:

```python
import warnings
from pydantic import ValidationError

async def store(self, data: TModel | dict[str, Any]) -> str:
    """Store data with model validation."""
    # Convert dict to model with deprecation warning
    if isinstance(data, dict):
        warnings.warn(
            f"Passing dict to {self.__class__.__name__}.store() is deprecated. "
            f"Use {TModel.__name__} model directly.",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            data = TModel.model_validate(data)
        except ValidationError as e:
            raise TierOperationError(f"Data validation failed: {e}") from e
    
    # Now data is guaranteed to be TModel
    # ... rest of implementation using data.field_name ...
```

**Files to Update:**
1. `src/memory/tiers/semantic_memory_tier.py` (line ~50) — **Start here (lowest risk)**
2. `src/memory/tiers/episodic_memory_tier.py` (line ~74)
3. `src/memory/tiers/working_memory_tier.py` (line ~127)
4. `src/memory/tiers/active_context_tier.py` (line ~113) — **Do last (performance-critical)**

#### Step 3: Create `EpisodeStoreInput` Model for L3

L3's `store()` currently accepts a complex dict with episode + embedding + entities.
Create a dedicated input model:

**File:** `src/memory/models.py`

```python
class EpisodeStoreInput(BaseModel):
    """
    Input model for L3 EpisodicMemoryTier.store() operation.
    
    Encapsulates the Episode model plus vector embedding and entity data
    required for dual-index storage (Qdrant + Neo4j).
    """
    episode: Episode
    embedding: list[float] = Field(..., min_length=1)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    
    @field_validator("embedding")
    @classmethod
    def validate_embedding_dimension(cls, v: list[float]) -> list[float]:
        """Ensure embedding has reasonable dimensions."""
        if len(v) < 64 or len(v) > 4096:
            raise ValueError(f"Embedding dimension {len(v)} outside valid range [64, 4096]")
        return v
```

Then update L3 tier: `class EpisodicMemoryTier(BaseTier[Episode])` but `store()` accepts
`EpisodeStoreInput | dict[str, Any]`.

**Note:** This is a deviation from pure generic symmetry, documented as intentional for
the dual-index architecture. The `retrieve()` returns `Episode`, not `EpisodeStoreInput`.

---

### Phase 2E.2: Migrate Engine Callers

**Goal:** Update engines to pass models directly instead of calling `.model_dump()`.

#### Current Pattern (to be deprecated):
```python
# promotion_engine.py line ~254
await self.l2.store(fact.model_dump())
```

#### Target Pattern:
```python
# Pass model directly - no .model_dump() needed
await self.l2.store(fact)
```

**Files to Update:**

| File | Line | Current | Target |
|------|------|---------|--------|
| `promotion_engine.py` | ~254 | `self.l2.store(fact.model_dump())` | `self.l2.store(fact)` |
| `promotion_engine.py` | ~284 | `self.l2.store(fallback_fact.model_dump())` | `self.l2.store(fallback_fact)` |
| `consolidation_engine.py` | ~284 | `self.l3.store({...})` | `self.l3.store(EpisodeStoreInput(...))` |
| `consolidation_engine.py` | ~361 | `self.l3.store({...})` | `self.l3.store(EpisodeStoreInput(...))` |
| `distillation_engine.py` | ~204 | `self.semantic_tier.store(doc)` | ✅ Already correct |

---

### Phase 2E.3: Update Agent/Tool Callers

**Goal:** Ensure all tool implementations use models.

**Files to Review:**

| File | Current Pattern | Action |
|------|-----------------|--------|
| `src/agents/tools/unified_tools.py` | `l1_tier.store(session_id, turn_data)` | Verify `turn_data` is `TurnData` |
| `src/evaluation/agent_wrapper.py` | `l1_tier.store(...)` | Update to pass `TurnData` model |

---

### Phase 2E.4: Update Tests

**Goal:** Add explicit type assertions and update dict-passing tests.

#### Pattern for Type Safety Assertions:

```python
import pytest
from src.memory.models import Fact, TurnData, Episode, KnowledgeDocument

async def test_retrieve_returns_typed_model(tier):
    """Verify retrieve() returns correct model type."""
    stored_id = await tier.store(valid_model_instance)
    result = await tier.retrieve(stored_id)
    
    assert result is not None
    assert isinstance(result, ExpectedModelType)  # <-- Add this assertion
    assert result.field_name == expected_value
```

#### Test Files to Update:

| File | Updates Needed |
|------|---------------|
| `tests/memory/test_active_context_tier.py` | Add `isinstance(result, TurnData)` checks |
| `tests/memory/test_working_memory_tier.py` | Add `isinstance(result, Fact)` checks |
| `tests/memory/test_episodic_memory_tier.py` | Add `isinstance(result, Episode)` checks |
| `tests/memory/test_semantic_memory_tier.py` | Add `isinstance(result, KnowledgeDocument)` checks |
| `tests/memory/engines/test_promotion_engine.py` | Update to pass `Fact` models |
| `tests/memory/engines/test_consolidation_engine.py` | Update to pass `EpisodeStoreInput` |

#### Handling Deprecation Warnings in Tests:

For tests that intentionally pass dicts (to verify backward compatibility):

```python
import warnings

def test_store_accepts_dict_with_deprecation_warning(tier):
    """Verify dict input works but emits deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        await tier.store({"field": "value", ...})
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
```

---

### Phase 2E.5: Mypy Strict Compliance

**Goal:** Ensure all changes pass `mypy --strict` checks.

#### Critical Mypy Patterns for This Refactoring:

1. **Generic Type Parameter Access:**
   ```python
   # Problem: Can't access TModel.__name__ in generic class
   # Solution: Use self.__class__.__orig_bases__ or pass model class explicitly
   
   class BaseTier[TModel: BaseModel](ABC):
       model_class: type[TModel]  # Store explicit reference
       
       def __init__(self, model_class: type[TModel], ...):
           self.model_class = model_class
   ```

2. **Union Type Narrowing:**
   ```python
   async def store(self, data: TModel | dict[str, Any]) -> str:
       if isinstance(data, dict):
           # mypy knows: data is dict[str, Any] here
           data = self.model_class.model_validate(data)
       # mypy knows: data is TModel here
       return data.some_field  # OK
   ```

3. **Avoiding `Any` Leakage:**
   ```python
   # Bad: dict[str, Any] leaks Any into operations
   content = data["content"]  # type: Any
   
   # Good: Model access is typed
   content = data.content  # type: str
   ```

4. **Pydantic ValidationError Import:**
   ```python
   from pydantic import ValidationError  # Not from pydantic.error_wrappers
   ```

#### Mypy Commands to Validate:

```bash
# Check specific tier files
/home/max/code/mas-memory-layer/.venv/bin/python -m mypy \
    src/memory/tiers/base_tier.py \
    src/memory/tiers/semantic_memory_tier.py \
    --strict

# Check all memory module
/home/max/code/mas-memory-layer/.venv/bin/python -m mypy \
    src/memory/ \
    --strict
```

---

## Rollout Order (Bottom-Up)

Execute phases in this order to minimize risk:

| Order | Tier | Risk Level | Rationale |
|-------|------|------------|-----------|
| 1 | L4 SemanticMemoryTier | 🟢 Low | Lowest volume, simplest structure |
| 2 | L2 WorkingMemoryTier | 🟢 Low | Already returns `Fact` models |
| 3 | L3 EpisodicMemoryTier | 🟡 Medium | Dual-index complexity; needs `EpisodeStoreInput` |
| 4 | L1 ActiveContextTier | 🟡 Medium | Performance-critical hot path |
| 5 | Engines | 🟢 Low | Mechanical updates after tiers done |
| 6 | Tests | 🟢 Low | Incremental with each tier |

---

## Verification Checklist

After completing each phase, verify:

- [ ] `mypy --strict` passes for modified files
- [ ] All existing tests pass: `pytest tests/ -v`
- [ ] Deprecation warnings emit correctly for dict input
- [ ] `isinstance()` assertions added to key tests
- [ ] No `Any` type leakage in public method signatures

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| L1 performance regression | Low | High | 500ms SLA acceptable; `model_construct()` if needed |
| L3 dual-index breakage | Medium | High | Careful review; preserve existing dict→model logic |
| Test churn | High | Low | Automate with search-replace patterns |
| Mypy generic edge cases | Medium | Medium | Reference Pydantic v2 mypy plugin docs |

---

## Definition of Done

Phase 2E is complete when:

1. ✅ All tier `store()` methods accept `TModel | dict[str, Any]`
2. ✅ Deprecation warnings emit for dict input
3. ✅ All engines pass models directly (no `.model_dump()`)
4. ✅ Tests include `isinstance()` type assertions
5. ✅ `mypy --strict` passes for entire `src/memory/` module
6. ✅ All 574+ tests pass
7. ✅ DEVLOG.md updated with completion entry

---

## Appendix: File Inventory

### Files Requiring Modification

| File | Changes |
|------|---------|
| `src/memory/tiers/base_tier.py` | Update `store()` signature and docstring |
| `src/memory/tiers/active_context_tier.py` | Update `store()` implementation |
| `src/memory/tiers/working_memory_tier.py` | Update `store()` implementation |
| `src/memory/tiers/episodic_memory_tier.py` | Update `store()`, handle `EpisodeStoreInput` |
| `src/memory/tiers/semantic_memory_tier.py` | Update `store()` implementation |
| `src/memory/models.py` | Add `EpisodeStoreInput` model |
| `src/memory/engines/promotion_engine.py` | Remove `.model_dump()` calls |
| `src/memory/engines/consolidation_engine.py` | Use `EpisodeStoreInput` |
| `tests/memory/test_*.py` | Add type assertions |

### Files Requiring Review Only

| File | Reason |
|------|--------|
| `src/agents/tools/unified_tools.py` | Verify model usage |
| `src/evaluation/agent_wrapper.py` | Verify model usage |
| `.github/instructions/source.instructions.md` | Update `store()` example |

---

## References

- [ADR-003: Four-Layer Memory Architecture](../ADR/003-four-layers-memory.md)
- [Research: Type-Safe Memory Tiers](../research/refactoring_memory_tiers_2_type_safe.md)
- [Pydantic v2 Mypy Plugin](https://docs.pydantic.dev/latest/integrations/mypy/)
- [Python 3.12 Generic Syntax (PEP 695)](https://peps.python.org/pep-0695/)
