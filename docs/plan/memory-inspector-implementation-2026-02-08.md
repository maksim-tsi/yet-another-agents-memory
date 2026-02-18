# Memory Inspector Implementation Plan

**Date:** 2026-02-08  
**Status:** ✅ Verified  
**Phase:** Complete (Integration Test Passed)

---

## Overview

Implementing "Glass Box" observability for the MAS Memory Layer by adding real-time telemetry and a `justification` field to data models. This enables transparent insight into memory tier operations and LLM-driven decisions.

---

## Completed Work

### 1. Data Model Updates ✅

| File | Change |
|------|--------|
| `src/memory/models.py` | Added `justification: str \| None` to `Fact` model |
| `src/memory/engines/topic_segmenter.py` | Added `justification: str \| None` to `TopicSegment` model |
| `src/memory/schemas/fact_extraction.py` | Added `justification` to LLM extraction schema and prompt |

### 2. UnifiedMemorySystem Created ✅

- **File:** `src/memory/system.py`
- **Features:**
  - Orchestrates L1-L4 tiers and engines
  - Feature flags for ablation (promotion, consolidation, distillation, telemetry)
  - `LifecycleStreamProducer` integration for telemetry emission
  - Facade API: `get_context_block()`, `query_memory()`, `run_promotion_cycle()`

### 3. Telemetry Infrastructure ✅

| Component | Change |
|-----------|--------|
| `src/memory/tiers/base_tier.py` | Added `telemetry_stream` param and `emit_telemetry()` helper |
| `src/memory/tiers/active_context_tier.py` | Propagates `telemetry_stream` to base |
| `src/memory/tiers/working_memory_tier.py` | Propagates `telemetry_stream` to base |
| `src/memory/tiers/episodic_memory_tier.py` | Propagates `telemetry_stream` to base |
| `src/memory/tiers/semantic_memory_tier.py` | Propagates `telemetry_stream` to base |

### 4. Engine Instrumentation ✅

| Engine | Telemetry Events |
|--------|------------------|
| `PromotionEngine` | `significance_scored`, `fact_promoted` |
| `FactExtractor` | Populates `justification` from LLM and fallback rules |

---

## In Progress

### 5. Integration Test 🚧

- **File:** `tests/integration/test_memory_inspector.py`
- **Purpose:** Verify end-to-end telemetry flow and justification persistence
- **Status:** Created, blocked on tier constructor alignment (just fixed)

---

## Remaining Work

| Task | Priority | Notes |
|------|----------|-------|
| Run integration test to validate telemetry | High | Re-run after L3/L4 tier constructor fix |
| Instrument `ConsolidationEngine` | Medium | Emit `episode_created` events |
| Instrument `DistillationEngine` | Medium | Emit `knowledge_synthesized` events |
| Add tier-level telemetry (store/retrieve) | Low | Optional for MVP |

---

## Verification Plan

1. **Automated Test:** `pytest tests/integration/test_memory_inspector.py`
   - Verifies `significance_scored` and `fact_promoted` events emitted
   - Verifies `justification` field populated in L2 facts

2. **Manual Smoke Test:**
   - Start `UnifiedMemorySystem` with real Redis/Postgres
   - Store turns, trigger promotion
   - Inspect Redis stream for telemetry events

---

## References

- **ADR:** `docs/ADR/008-benchmark-and-inspector-adoption.md`
- **Requirements:** `docs/requirements/req-02-memory-inspector.md`
- **Concept:** `docs/concept-02-memory-inspector.md`
