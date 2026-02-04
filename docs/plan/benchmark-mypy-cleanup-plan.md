# Benchmark Package Mypy Cleanup Plan

**Created:** 2026-02-04  
**Status:** Planned  
**Estimated Effort:** 6-7 hours  
**Scope:** 129 mypy errors across 23 files in `benchmarks/`

---

## Executive Summary

This plan addresses making the `benchmarks/` package mypy-compliant while integrating
with the existing pre-commit workflow. The approach uses **minimal stubs** for external
dependencies, **lenient overrides** for benchmark code, and **strict typing at boundary
objects** to ensure AIMS 2025 research reproducibility.

### Related Documentation

- **Visibility Improvements:** [`benchmarks/goodai-ltm-benchmark/docs/improvement-plan.md`](../../benchmarks/goodai-ltm-benchmark/docs/improvement-plan.md)
- **Memory Refactoring:** [`docs/plan/memory-refactoring-plan-04022026.md`](memory-refactoring-plan-04022026.md)

---

## Error Distribution Summary

| Error Category | Count | Priority |
|----------------|-------|----------|
| `= None` dataclass defaults | ~20 | P1 |
| `import-untyped` | ~30 | P2 |
| Missing return annotations | ~40 | P3 |
| `union-attr` (null access) | ~15 | P4 |
| Misc (assignment, var-annotated) | ~24 | P5 |
| **Total** | **~129** | |

---

## Architectural Decisions

### Decision 1: Stubs vs. Ignores for `goodai-ltm`

**Decision:** Create minimal stub files in `stubs/goodai/`

**Rationale:**
- Prevents "ignore-rot" where future changes go unverified
- Enables IDE autocomplete for `LTMAgent`, `RetrievedMemory`, etc.
- Catches API drift if `goodai-ltm` library changes
- Only ~4 stub files needed for actual usage surface

**Alternative Rejected:** Per-import `# type: ignore` across 23 files would be harder to maintain.

### Decision 2: Strictness Level

**Decision:** Lenient overrides for benchmarks, strict for boundary objects

**Rationale:**
- Benchmark runner code can use lenient rules (`disallow_untyped_defs = false`)
- **Boundary objects** (code transforming `src/` models like `Fact`, `Episode`) must remain strict
- Critical for AIMS 2025 reproducibility—prevents "silent data corruption" where benchmarks test malformed data

**Strict Boundary Files:**
- `benchmarks/goodai-ltm-benchmark/model_interfaces/mas_memory_adapters.py`
- Any code importing from `src/memory/models.py`

### Decision 3: CI Integration

**Decision:** Single `pyproject.toml` config with per-module overrides

**Rationale:**
- Avoids configuration drift between local and CI environments
- One `mypy .` command validates entire repo
- Pre-commit hook needs no special flags
- Per-module sections apply appropriate strictness automatically

---

## Implementation Phases

### Phase 1: Foundation (30 minutes)

#### 1.1 Install Type Stub Packages

Add to `requirements-test.txt`:
```
types-click
types-PyYAML
types-requests
```

*Status: ✅ Partially complete (`types-PyYAML` installed)*

#### 1.2 Update pyproject.toml

Add benchmark-specific mypy configuration:

```toml
[[tool.mypy.overrides]]
module = "benchmarks.*"
disallow_untyped_defs = false
warn_return_any = false
ignore_missing_imports = true

# Strict for boundary objects (MAS model transformations)
[[tool.mypy.overrides]]
module = "benchmarks.goodai-ltm-benchmark.model_interfaces.mas_memory_adapters"
disallow_untyped_defs = true
warn_return_any = true
```

Add stubs path:
```toml
[tool.mypy]
mypy_path = "stubs"
```

---

### Phase 2: Create goodai-ltm Stubs (1 hour)

Create minimal stub files covering actual usage:

```
stubs/
├── goodai/
│   ├── __init__.pyi
│   ├── helpers/
│   │   ├── __init__.pyi
│   │   └── json_helper.pyi
│   └── ltm/
│       ├── __init__.pyi
│       ├── agent.pyi
│       └── mem/
│           ├── __init__.pyi
│           └── base.pyi
```

#### Stub Content Examples

**`stubs/goodai/ltm/agent.pyi`:**
```python
from typing import Any
from enum import Enum

class LTMAgentVariant(Enum):
    QA_HNSW = "qa_hnsw"
    QA_ST = "qa_st"
    # Add variants as needed

class LTMAgent:
    def __init__(self, variant: LTMAgentVariant, **kwargs: Any) -> None: ...
    def reply(self, message: str) -> str: ...
    def reset(self) -> None: ...
```

**`stubs/goodai/helpers/json_helper.pyi`:**
```python
from typing import Any

def sanitize_and_parse_json(text: str) -> Any: ...
```

---

### Phase 3: Fix Dataclass Defaults (30 minutes)

Change `field: Type = None` → `field: Type | None = None`

#### Files and Locations

| File | Lines | Fields |
|------|-------|--------|
| `dataset_interfaces/interface.py` | 69, 114, 124, 274, 277, 323 | `filler_response`, `expected_responses`, `random`, `action`, `dataset_generator` |
| `reporting/results.py` | 22-23 | `tokens`, `characters` |
| `model_interfaces/llm_interface.py` | 22-23 | `max_prompt_size`, `model` |
| `runner/scheduler.py` | 64-65 | `master_log`, `progress_dialog` |
| `model_interfaces/model.py` | 15-21 | Various fields |

#### Pattern

```python
# BEFORE
@dataclass
class TestExample:
    filler_response: str = None  # Error!

# AFTER
@dataclass
class TestExample:
    filler_response: str | None = None  # Correct
```

---

### Phase 4: Add Import Ignores (45 minutes)

Add `# type: ignore[import-untyped]` for stubless packages:

| Package | Files Affected |
|---------|----------------|
| `pystache` | `datasets/*.py` (locations, shopping, etc.) |
| `tiktoken` | `utils/llm.py`, `model_interfaces/gemini_interface.py` |
| `time_machine` | `runner/scheduler.py` |
| `termcolor` | `utils/ui.py` |
| `faker` | `datasets/*.py` |

#### Pattern

```python
import pystache  # type: ignore[import-untyped]
from faker import Faker  # type: ignore[import-untyped]
```

---

### Phase 5: Add Return Type Annotations (2-3 hours)

Priority order:

#### 5.1 Utility Functions (`utils/files.py`)

```python
# BEFORE
def gather_testdef_files(run_name: str = "*", dataset_name: str = "*"):
    return glob(...)

# AFTER
def gather_testdef_files(run_name: str = "*", dataset_name: str = "*") -> list[str]:
    return glob(...)
```

#### 5.2 ChatSession Methods (`model_interfaces/`)

All `reply()`, `reset()`, `get_stats()` methods across:
- `llm_interface.py`
- `gemini_interface.py`
- `huggingface_interface.py`
- `base_ltm_agent.py`

#### 5.3 Scheduler Methods (`runner/scheduler.py`)

- `run_tests() -> None`
- `run_single_test() -> TestResult`
- `_setup_logging() -> None`

---

### Phase 6: Add Null Guards (1 hour)

Insert assertions or conditionals for optional attribute access:

#### Pattern A: Assertion (for known-initialized state)

```python
# scheduler.py
def run_tests(self) -> None:
    assert self.master_log is not None, "master_log must be initialized before run"
    self.master_log.load()
```

#### Pattern B: Conditional (for truly optional)

```python
if self.progress_dialog is not None:
    self.progress_dialog.update(progress)
```

#### Files

| File | Attributes |
|------|------------|
| `runner/scheduler.py` | `master_log`, `progress_dialog` |
| `dataset_interfaces/interface.py` | `action`, `dataset_generator` |

---

### Phase 7: Validate Boundary Objects (30 minutes)

Ensure strict typing in MAS model adapters:

**File:** `benchmarks/goodai-ltm-benchmark/model_interfaces/mas_memory_adapters.py`

Verify:
- All functions have explicit return types
- All parameters are typed
- `Fact`, `Episode`, `KnowledgeDocument` imports are used correctly
- No `Any` types for MAS model transformations

---

## Integration with Visibility Improvements

The visibility improvements from [`improvement-plan.md`](../../benchmarks/goodai-ltm-benchmark/docs/improvement-plan.md)
should be implemented with mypy compliance from the start:

| Visibility Feature | Mypy Consideration |
|--------------------|--------------------|
| `tqdm` progress reporting | `tqdm` has type stubs—no issues |
| `turn_metrics.jsonl` output | Use `TypedDict` for metric records |
| Watchdog with `run_error.json` | Type the diagnostic dict structure |
| Grafana dashboard template | JSON only—no Python typing needed |
| Phoenix trace alignment | OpenTelemetry has stubs—verify imports |

### Recommended Metric TypedDict

```python
from typing import TypedDict

class TurnMetric(TypedDict):
    timestamp: str
    test_id: str
    turn_id: int
    llm_ms: float
    storage_ms: float
    total_ms: float
    tokens_in: int
    tokens_out: int
    status: str  # "success" | "error"
```

---

## Validation Checklist

- [ ] `mypy benchmarks/` passes with zero errors
- [ ] Pre-commit hook passes on benchmark files
- [ ] IDE autocomplete works for `goodai-ltm` classes
- [ ] `mas_memory_adapters.py` passes strict mypy checks
- [ ] No `# type: ignore` without specific error code
- [ ] Type stubs cover all used `goodai-ltm` APIs

---

## Effort Summary

| Phase | Task | Time |
|-------|------|------|
| 1 | Foundation (stubs install, pyproject.toml) | 30 min |
| 2 | Create `stubs/goodai/` | 1 hour |
| 3 | Fix dataclass defaults | 30 min |
| 4 | Add import ignores | 45 min |
| 5 | Return type annotations | 2-3 hours |
| 6 | Null guards | 1 hour |
| 7 | Validate boundary objects | 30 min |
| **Total** | | **6-7 hours** |

---

## References

- [Mypy Per-Module Configuration](https://mypy.readthedocs.io/en/stable/config_file.html#per-module-and-global-options)
- [PEP 561: Distributing and Packaging Type Information](https://peps.python.org/pep-0561/)
- [Pydantic v2 Mypy Integration](https://docs.pydantic.dev/latest/integrations/mypy/)
- [Visibility Improvement Plan](../../benchmarks/goodai-ltm-benchmark/docs/improvement-plan.md)
