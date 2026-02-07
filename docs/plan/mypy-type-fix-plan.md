# Mypy Type Error Remediation Plan

**Date:** 2026-02-04  
**Status:** Completed  
**Initial Errors:** 119 across 13 files  
**Current Errors:** 0 (all resolved)
**Estimated Remaining Effort:** 0 hours  

## Progress Summary

### Completed Fixes (Phase 1)
| Category | Files Fixed | Errors Resolved |
|----------|-------------|-----------------|
| Dict Variance (Mapping) | `base_tier.py` | 4 |
| JSONEncodeError typo | `redis_adapter.py` | 1 |
| Unused type:ignore | `postgres_adapter.py` | 5 |
| Engine Stats Typing | `promotion_engine.py`, `consolidation_engine.py` | 12 |
| Redis Proxy Methods | `redis_adapter.py` | 5 |
| **Total Phase 1** | **5 files** | **~47 errors** |

### Remaining Issues (Phase 2)
1.  **Missing Return Statements** - 21 errors (Adapter abstract methods or loose typing)
2.  **Unused Type Ignores** - 3 errors (Config fix resolved these)

## Implementation Strategy (Option A)

The remediation will **extend adapter APIs** to match existing tier usage. This avoids large-scale tier refactoring while preserving the current adapter query dictionary pattern. New adapter methods will be added as explicit, typed wrappers where tiers currently depend on non-existent signatures.

## Batch Plan and Progress Tracking

### Batch Overview

| Batch | Scope | Primary Files | Status |
|-------|-------|---------------|--------|
| 1 | Postgres adapter methods | `src/storage/postgres_adapter.py` | Complete |
| 2 | Typesense adapter methods | `src/storage/typesense_adapter.py` | Complete |
| 3 | Qdrant adapter signature enhancements | `src/storage/qdrant_adapter.py` | Complete |
| 4 | Redis/Neo4j type fixes | `src/storage/redis_adapter.py`, `src/storage/neo4j_adapter.py` | Complete |
| 5 | Tier alignment to new adapters | `src/memory/tiers/*` | Complete |
| 6 | Engine and model typing fixes | `src/memory/engines/*`, `src/memory/models.py`, `src/memory/ciar_scorer.py` | Complete |
| 7 | Per-module mypy override | `pyproject.toml` | Revised & Verified |
| 8 | Final Cleanup & Config Hardening | Adapters & Engines | Pending |

### Batch 1: Postgres Adapter Methods
**Goal:** Implement `execute()`, `update()`, and `delete_by_filters()` (or equivalent) to match tier usage; add `order_by` support to `query()`.

**Checklist:**
- [x] Add `execute(sql: str, *params: Any) -> list[dict[str, Any]]`
- [x] Add `update(table: str, filters: dict[str, Any], data: dict[str, Any]) -> bool`
- [x] Add `delete_by_filters(table: str, filters: dict[str, Any]) -> bool`
- [x] Extend `query()` with `order_by: str | None`
- [x] Fix tuple assignment type mismatch (line ~569)
- [x] Commit: `feat(storage): add postgres adapter CRUD methods`

### Batch 2: Typesense Adapter Methods
**Goal:** Implement document-level wrappers and a keyword-args search overload to match tier usage.

**Checklist:**
- [x] Add `get_document(collection_name: str, document_id: str) -> dict[str, Any] | None`
- [x] Add `update_document(collection_name: str, document_id: str, document: dict[str, Any]) -> bool`
- [x] Add `delete_document(collection_name: str, document_id: str) -> bool`
- [x] Add keyword-args `search()` overload returning raw response with `hits`
- [x] Fix return typing at lines ~180, ~207, ~209
- [x] Commit: `feat(storage): add typesense adapter document methods`

### Batch 3: Qdrant Adapter Signature Enhancements
**Goal:** Accept both dict-style and keyword-args search/delete calls, with correct filter typing.

**Checklist:**
- [x] Update `search()` to accept kwargs and map to dict query
- [x] Update `delete()` to accept `collection_name` and `point_ids`
- [x] Fix filter union typing at lines ~527-529, ~563
- [x] Fix results list typing at lines ~682-687
- [x] Commit: `feat(storage): enhance qdrant adapter search/delete signatures`

### Batch 4: Redis and Neo4j Type Fixes
**Goal:** Resolve awaitable union types and optional attribute access patterns.

**Checklist:**
- [x] Add explicit casts on Redis await results (e.g., `int(await ...)`, `bool(...)`)
- [x] Ensure `self.client` and `self.driver` null guards before access
- [x] Commit: `fix(storage): redis/neo4j type annotations`

### Batch 5: Tier Alignment
**Goal:** Align tier calls to new adapter methods without altering domain logic.

**Checklist:**
- [x] Update `working_memory_tier.py` to use new Postgres adapter methods
- [x] Update `semantic_memory_tier.py` to use new Typesense adapter methods
- [x] Update `episodic_memory_tier.py` to use updated Qdrant adapter methods
- [x] Update `active_context_tier.py` to use Postgres delete wrapper
- [x] Commit: `fix(memory): align tier calls with adapter methods`

### Batch 6: Engines and Models
**Goal:** Correct typing for LLM responses, optional tier access, and remove stale ignores.

**Checklist:**
- [x] Add explicit `llm_client` type annotations
- [x] Add null guards for optional tier attributes
- [x] Fix `LLMResponse` usage (use `.content` or equivalent)
- [x] Fix `models.py` validator return type
- [x] Remove unused `# type: ignore` comments
- [x] Commit: `fix(memory): engine and model type annotations`

### Batch 7: Per-Module Mypy Override
**Goal:** Resolve `AssertionError: Cannot find module for google` via per-module override.

**Checklist:**
- [x] Add `[[tool.mypy.overrides]]` for `module = "google.*"` with `ignore_errors = true`
- [x] Add `namespace_packages = true` and `explicit_package_bases = true` to `[tool.mypy]`
- [x] Add manual cache clearing step to workflows
- [x] Commit: `chore: harden mypy config for namespace packages`

### Batch 8: Final Cleanup & Config Hardening
**Goal:** Fix missing return statements in adapters and remove now-redundant type ignores.

**Checklist:**
- [x] Fix `Missing return statement` in `RedisAdapter` (Added unreachable assertions)
- [x] Fix `Missing return statement` in `Neo4jAdapter` (Added unreachable assertions)
- [x] Fix `Missing return statement` in `TypesenseAdapter` (Added unreachable assertions)
- [x] Fix `Missing return statement` in `QdrantAdapter` (Added unreachable assertions)
- [x] Remove unused `type: ignore` in `ciar_scorer.py`
- [x] Remove unused `type: ignore` in `knowledge_synthesizer.py`
- [x] Remove unused `type: ignore` in `distillation_engine.py`

---

## Error Categorization

### Category 1: Redis Async Return Type Ambiguity (25 errors)
**Files:** `src/storage/redis_adapter.py`  
**Root Cause:** Redis async client returns `Awaitable[T] | T` union types that mypy cannot narrow without explicit handling.

**Error Patterns:**
- `[misc]` Incompatible types in "await" (actual type "Awaitable[int] | int", expected type "Awaitable[Any]")
- `[no-any-return]` Returning Any from function declared to return "bool"
- `[union-attr]` Item "None" of "Redis | None" has no attribute "lrange"

**Fix Strategy:**
1. Add explicit null checks before accessing `self.client` methods
2. Use `cast()` or explicit type narrowing for await results
3. Wrap return values: `return bool(result)` instead of raw `return result`

**Example Fix:**
```python
# Before (error: Returning Any from function declared to return "bool")
return await self.client.exists(key)

# After (explicit cast)
result = await self.client.exists(key)
return bool(result)
```

---

### Category 2: BaseTier Return Type Override Mismatch (8 errors)
**Files:** `active_context_tier.py`, `working_memory_tier.py`, `episodic_memory_tier.py`, `semantic_memory_tier.py`  
**Root Cause:** Tier implementations return domain models (`Fact`, `Episode`, `KnowledgeDocument`) instead of `dict[str, Any]` as declared in `BaseTier`.

**Error Pattern:**
- `[override]` Return type "Coroutine[Any, Any, Fact | None]" of "retrieve" incompatible with return type "Coroutine[Any, Any, dict[str, Any] | None]" in supertype

**Fix Strategy:**
Refactor `BaseTier` to use generics:
```python
from typing import TypeVar, Generic

T = TypeVar("T", bound=dict[str, Any])

class BaseTier(ABC, Generic[T]):
    @abstractmethod
    async def retrieve(self, identifier: str) -> T | None:
        pass
```

Or, keep dict returns and have tiers call `.model_dump()` internally:
```python
async def retrieve(self, identifier: str) -> dict[str, Any] | None:
    fact = await self._retrieve_fact(identifier)
    return fact.model_dump() if fact else None
```

**Decision:** Option 2 (dict returns) maintains API stability. Each tier should convert domain objects to dicts at the boundary.

---

### Category 3: Adapter Method Signature Mismatch (18 errors)
**Files:** `semantic_memory_tier.py`, `episodic_memory_tier.py`, `working_memory_tier.py`  
**Root Cause:** Tier code calls adapter methods with incorrect signatures. Adapters use `query: dict[str, Any]` pattern but tiers call with kwargs like `collection_name=`, `query_by=`, `limit=`.

**Error Patterns:**
- `[call-arg]` Unexpected keyword argument "collection_name" for "search" of "QdrantAdapter"
- `[call-arg]` Unexpected keyword argument "filters" for "delete" of "PostgresAdapter"
- `[arg-type]` Argument "query" to "search" has incompatible type "str"; expected "dict[str, Any]"

**Fix Strategy:**
Align tier calls with adapter signatures:
```python
# Before (error: unexpected keyword args)
await self.qdrant.search(
    collection_name=self.collection_name,
    query_vector=embedding,
    limit=limit,
    filter_dict=filters,
)

# After (use dict query structure)
query = {
    "collection_name": self.collection_name,
    "query_vector": embedding,
    "limit": limit,
    "filter_dict": filters,
}
await self.qdrant.search(query)
```

**Alternative:** Extend adapter signatures to accept both patterns with overloaded methods.

---

### Category 4: Missing Adapter Methods (8 errors)
**Files:** `semantic_memory_tier.py`, `working_memory_tier.py`  
**Root Cause:** Tier code calls adapter methods that don't exist.

**Error Pattern:**
- `[attr-defined]` "TypesenseAdapter" has no attribute "get_document"
- `[attr-defined]` "TypesenseAdapter" has no attribute "update_document"
- `[attr-defined]` "PostgresAdapter" has no attribute "execute"
- `[attr-defined]` "PostgresAdapter" has no attribute "update"

**Fix Strategy:**
1. Add missing methods to adapters, OR
2. Replace with existing adapter API calls

**Decision:** Add wrapper methods to adapters for domain-specific operations. This keeps tier code clean while maintaining adapter encapsulation.

---

### Category 5: Dict Variance Issues (4 errors)
**Files:** `working_memory_tier.py`, `semantic_memory_tier.py`  
**Root Cause:** `dict` is invariant in value type, but code passes `dict[str, PostgresAdapter]` where `dict[str, StorageAdapter]` expected.

**Error Pattern:**
- `[arg-type]` Argument 1 to "__init__" of "BaseTier" has incompatible type "dict[str, PostgresAdapter]"; expected "dict[str, StorageAdapter]"
- Note: "dict" is invariant -- see mypy docs

**Fix Strategy:**
Use `Mapping` (covariant) instead of `dict` in BaseTier signature:
```python
from collections.abc import Mapping

class BaseTier(ABC):
    def __init__(
        self,
        storage_adapters: Mapping[str, StorageAdapter],  # Changed from dict
        ...
    ):
```

---

### Category 6: Qdrant Filter Type Mismatch (7 errors)
**Files:** `src/storage/qdrant_adapter.py`  
**Root Cause:** Building `Filter` with `list[FieldCondition]` but Qdrant SDK expects broader union type.

**Error Pattern:**
- `[arg-type]` Argument "must" to "Filter" has incompatible type "list[FieldCondition] | None"; expected "list[FieldCondition | IsEmptyCondition | ...] | None"

**Fix Strategy:**
Annotate filter lists with the correct union type:
```python
from qdrant_client.http.models import FieldCondition, IsEmptyCondition, IsNullCondition, HasIdCondition, NestedCondition, Filter

FilterConditionType = FieldCondition | IsEmptyCondition | IsNullCondition | HasIdCondition | NestedCondition | Filter

must_conditions: list[FilterConditionType] | None = [...]
```

---

### Category 7: Engine Counter Type Issues (12 errors)
**Files:** `promotion_engine.py`, `consolidation_engine.py`  
**Root Cause:** Stats dict values are `object` type, not `int`. Arithmetic operations fail.

**Error Pattern:**
- `[operator]` Unsupported operand types for + ("object" and "int")

**Fix Strategy:**
Add explicit type annotations for stats dicts:
```python
stats: dict[str, int | str] = {
    "turns_retrieved": 0,
    "segments_created": 0,
    ...
}
```

---

### Category 8: LLM Client Type Issues (8 errors)
**Files:** `knowledge_synthesizer.py`, `distillation_engine.py`  
**Root Cause:** `llm_client` attribute type cannot be determined; `LLMResponse` access patterns incorrect.

**Error Patterns:**
- `[has-type]` Cannot determine type of "llm_client"
- `[attr-defined]` "LLMResponse" has no attribute "strip"
- `[no-any-return]` Returning Any from function

**Fix Strategy:**
1. Add explicit type annotation for `llm_client` attribute
2. Access `.content` or correct attribute on `LLMResponse`

---

### Category 9: Null Safety Issues (12 errors)
**Files:** `distillation_engine.py`, `episodic_memory_tier.py`, `neo4j_adapter.py`  
**Root Cause:** Accessing methods on `T | None` without null checks.

**Error Patterns:**
- `[union-attr]` Item "None" of "EpisodicMemoryTier | None" has no attribute "query"
- `[union-attr]` Item "None" of "AsyncDriver | None" has no attribute "session"

**Fix Strategy:**
Add null guards:
```python
if self.l3 is not None:
    await self.l3.query(...)
```

---

### Category 10: Miscellaneous (7 errors)
- Unused `type: ignore` comments in `postgres_adapter.py`
- `yaml` import-untyped errors
- Tuple assignment type mismatch
- `json.JSONEncodeError` typo (should be `JSONDecodeError`)

---

## Implementation Order

| Priority | Category | Files | Est. Time | Risk |
|----------|----------|-------|-----------|------|
| 1 | Cat 5: Dict Variance | `base_tier.py` | 15 min | Low |
| 2 | Cat 7: Counter Types | `promotion_engine.py`, `consolidation_engine.py` | 30 min | Low |
| 3 | Cat 1: Redis Async | `redis_adapter.py` | 45 min | Medium |
| 4 | Cat 9: Null Safety | Multiple | 30 min | Low |
| 5 | Cat 10: Misc | Multiple | 20 min | Low |
| 6 | Cat 6: Qdrant Filters | `qdrant_adapter.py` | 30 min | Medium |
| 7 | Cat 3: Signature Mismatch | Tiers | 60 min | High |
| 8 | Cat 4: Missing Methods | Adapters | 45 min | High |
| 9 | Cat 8: LLM Client | Engines | 30 min | Medium |
| 10 | Cat 2: BaseTier Generics | All tiers | 45 min | High |

---

## Guidelines for Future Development

### G1: Redis Async Pattern
Always explicitly type and narrow Redis return values:
```python
result: int = int(await self.client.exists(key))
```

### G2: Null Checks Before Access
Never access optional attributes without guards:
```python
if self.client is None:
    raise StorageConnectionError("Not connected")
```

### G3: Adapter Method Signatures
All adapter `search()`, `delete()`, `update()` methods accept `dict[str, Any]` query parameter. Tiers MUST construct query dicts, not pass kwargs.

### G4: Use Mapping for Covariance
When accepting adapter collections, use `Mapping[str, StorageAdapter]` not `dict[str, StorageAdapter]`.

### G5: Stats Dict Typing
Always annotate stats/counter dicts:
```python
stats: dict[str, int] = {"count": 0}
stats["count"] += 1  # Now type-safe
```

### G6: Domain Object Boundaries
Tiers return `dict[str, Any]` at API boundaries. Use `.model_dump()` for Pydantic models.

### G7: LLM Response Handling
Access `LLMResponse.content` not the response object directly:
```python
response = await self.llm_client.generate(prompt)
text = response.content  # Not response.strip()
```

---

## Verification Checklist

After all fixes:
- [ ] `mypy src/memory src/storage --namespace-packages --ignore-missing-imports` reports 0 errors
- [ ] `ruff check .` passes
- [ ] `pytest tests/ -v -m "not llm_real"` all pass
- [ ] Pre-commit hook succeeds
- [ ] Guidelines added to `.github/instructions/source.instructions.md`

---

## Related Documents

- [ADR-003: Four-Layer Memory Architecture](../ADR/003-four-layers-memory.md)
- [Lessons Learned Register](../lessons-learned.md)
- [Source Code Instructions](../../.github/instructions/source.instructions.md)
