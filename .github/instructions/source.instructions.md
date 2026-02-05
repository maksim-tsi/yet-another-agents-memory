---
applyTo: "src/**/*.py"
---

# Source Code Implementation Patterns

## Async-First Architecture

All storage and tier methods are `async def`. Use `asyncio` patterns throughout:

```python
async def store(self, data: Dict[str, Any]) -> str:
    async with self.adapters['redis'].health_check() as health:
        ...
```

## Dual Storage Pattern (L1, L2)

Tiers use write-through cache: primary (Redis/hot) + fallback (PostgreSQL/cold):

```python
# Write to both storage layers
# Read from Redis first with graceful fallback to PostgreSQL
# See src/memory/tiers/active_context_tier.py:120-150 for reference
```

**Pattern**:
1. Write operations go to both Redis (hot) and PostgreSQL (cold)
2. Read operations try Redis first, fall back to PostgreSQL on failure
3. Implement graceful degradation if primary storage fails

## Dual Indexing (L3)

Episodic memory coordinates Qdrant (vector) + Neo4j (graph) with linked IDs:

```python
# Store in both: vector for similarity search, graph for relationships
# Maintain ID linkage between Qdrant and Neo4j records
# See src/memory/tiers/episodic_memory_tier.py:71-115 for reference
```

**Pattern**:
1. Generate a single episode ID
2. Store vector embedding in Qdrant with episode ID
3. Store graph relationships in Neo4j with same episode ID
4. Ensure both operations succeed or roll back

## CIAR Scoring Formula

Facts are promoted from L1→L2 based on CIAR score calculation (config in `config/ciar_config.yaml`):

```python
CIAR = (certainty × impact) × age_decay × recency_boost
# Default promotion threshold: 0.6 (configurable)
# See src/memory/ciar_scorer.py:85-130 for implementation
```

**Components**:
- **Certainty** (0.0-1.0): Confidence in fact accuracy
- **Impact** (0.0-1.0): Importance/relevance of the fact
- **Age Decay** (0.1-1.0): Time-based decay factor
- **Recency Boost** (1.0-1.3): Access-based reinforcement

## BaseTier Pattern

All memory tiers inherit from `BaseTier` (abstract interface):

```python
from src.memory.tiers.base_tier import BaseTier

class MyTier(BaseTier):
    async def initialize(self) -> None:
        """Initialize storage adapters and tier-specific resources."""
        pass
    
    async def store(self, data: Dict[str, Any]) -> str:
        """Store data and return unique identifier."""
        pass
    
    async def retrieve(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by identifier."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check tier and adapter health status."""
        pass
```

**BaseTier provides**:
- Manages `storage_adapters` dict
- Manages optional `metrics_collector`
- Provides config management
- See `src/memory/tiers/base_tier.py` for full interface

## Pydantic v2 Data Models

Use Pydantic v2 for all data models with strict validation:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime

class MyModel(BaseModel):
    """Model description."""
    
    field_name: str = Field(..., description="Field description")
    optional_field: Optional[int] = Field(default=None, description="Optional field")
    
    @field_validator('field_name')
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validate field_name."""
        if not v:
            raise ValueError("field_name cannot be empty")
        return v
```

**Key patterns**:
- Use `Field()` for all fields with descriptions
- Use `field_validator` for custom validation (not `@validator`)
- All timestamps should use `datetime` with timezone awareness
- Use proper type hints (`Optional`, `Dict`, `List`, etc.)

## Storage Exception Hierarchy

Use the storage exception hierarchy for consistent error handling:

```python
from src.storage.base import (
    StorageError,           # Base exception
    StorageConnectionError, # Connection failures
    StorageQueryError,      # Query execution failures
    StorageDataError,       # Data validation errors
    StorageTimeoutError,    # Operation timeouts
    StorageNotFoundError    # Resource not found
)

try:
    await adapter.store(data)
except StorageConnectionError as e:
    logger.error(f"Connection failed: {e}")
    # Handle connection failure
except StorageDataError as e:
    logger.error(f"Data validation failed: {e}")
    # Handle validation error
except StorageError as e:
    logger.error(f"Storage operation failed: {e}")
    # Handle general storage error
```

**Exception hierarchy**:
- `StorageError` - Base class, catch for any storage error
- `StorageConnectionError` - Cannot connect to backend
- `StorageQueryError` - Query/operation execution failed
- `StorageDataError` - Data validation or integrity error
- `StorageTimeoutError` - Operation exceeded time limit
- `StorageNotFoundError` - Requested resource doesn't exist

## Metrics Instrumentation

Enable metrics on any adapter for observability:

```python
from src.storage.metrics.collector import MetricsCollector

config = {
    'uri': 'bolt://localhost:7687',
    'metrics': {
        'enabled': True,
        'max_history': 1000,
        'percentiles': [50, 95, 99]
    }
}

adapter = Neo4jAdapter(config)

# Metrics are automatically collected for all operations
# Export metrics in multiple formats
metrics = adapter.get_metrics()
metrics.export_json("results.json")
metrics.export_csv("results.csv")
metrics.export_prometheus()  # Gauge format
```

**Metrics collected**:
- Operation timing (avg, min, max, percentiles)
- Throughput (ops/sec, bytes/sec)
- Success/failure rates
- Backend-specific metrics

## Code Style Guidelines

- **Type Hints**: All functions must have return types and parameter types
- **Docstrings**: Use Google style with Args, Returns, Raises, Examples sections
- **Logging**: Use `logger = logging.getLogger(__name__)` pattern at module level
- **Imports**: Group imports (stdlib, third-party, local) with blank lines between
- **Async Context Managers**: Use `async with` for resource management
- **Error Messages**: Include context (operation, parameters, state) in error messages

## Mypy Type Safety Guidelines

Follow these patterns to ensure mypy compliance:

### Redis Async Return Types
Redis asyncio methods return `Awaitable[T] | T` union types. Always use explicit casts:

```python
# Bad - mypy error: Returning Any from function declared to return "bool"
return await self.client.exists(key)

# Good - explicit type cast
result = await self.client.exists(key)
return int(result) > 0

# For proxy methods wrapping Redis calls
async def llen(self, key: str) -> int:
    result = await self.client.llen(key)
    return int(result)  # Explicit cast
```

### Null Safety Checks
Always guard against `None` before accessing optional attributes:

```python
# Bad - mypy error: Item "None" of "T | None" has no attribute "method"
await self.client.lrange(key, 0, -1)

# Good - null guard first
if not self.client:
    raise StorageConnectionError("Not connected")
result = await self.client.lrange(key, 0, -1)
```

### Dict Covariance for Adapter Collections
Use `Mapping` instead of `dict` when accepting adapter collections:

```python
from collections.abc import Mapping

# Bad - mypy error: dict is invariant in value type
def __init__(self, adapters: dict[str, StorageAdapter]): ...

# Good - Mapping is covariant
def __init__(self, adapters: Mapping[str, StorageAdapter]): ...
```

### Stats/Counter Dict Typing
Always annotate stats dicts to enable arithmetic operations:

```python
# Bad - stats values become object type, += 1 fails
stats = {"count": 0, "errors": 0}
stats["count"] += 1  # mypy error: unsupported operand types

# Good - explicit type annotation
stats: dict[str, int] = {"count": 0, "errors": 0}
stats["count"] += 1  # type-safe

# For mixed int/str stats, use helper function
stats: dict[str, int | str] = {"session_id": sid, "count": 0}
def inc(key: str, amount: int = 1) -> None:
    stats[key] = int(stats.get(key, 0)) + amount  # type: ignore[arg-type]
inc("count")
```

### Adapter Method Signatures
Storage adapters use `dict[str, Any]` query pattern. Call adapters correctly:

```python
# Bad - mypy error: unexpected keyword argument
await self.adapter.search(collection_name="x", limit=10)

# Good - pass query dict
query = {"collection_name": "x", "limit": 10}
await self.adapter.search(query)
```

### Type Ignore Comments
Use sparingly and with specific error codes:

```python
# Bad - suppresses all errors
result = something()  # type: ignore

# Good - specific error code
from yaml import safe_load  # type: ignore[import-untyped]
```
