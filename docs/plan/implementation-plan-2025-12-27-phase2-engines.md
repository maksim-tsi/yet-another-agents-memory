# Phase 2 Lifecycle Engines Implementation Plan

**Date**: 2025-12-27
**Status**: In Progress
**Reference Spec**: [spec-phase2-memory-tiers.md](../specs/spec-phase2-memory-tiers.md)

## Overview

This plan details the implementation steps for the **Lifecycle Engines** (Phase 2B-2D) of the MAS Memory Layer. These engines are responsible for the autonomous flow of information between memory tiers, transforming raw context into structured facts, episodes, and distilled knowledge.

The implementation follows the architecture defined in **ADR-003** and the **Phase 2 Specification**.

---

## Prerequisites

- [x] **Update Documentation**: Update `.github/copilot-instructions.md` to reflect that `LLM Client` is implemented (currently marked as missing).
- [x] **Engine Foundation**: Create `src/memory/engines/` directory.

---

## Phase 2B: Promotion Engine (L1 → L2)

**Objective**: Automate the extraction of significant facts from Active Context (L1) and promote them to Working Memory (L2).

**Spec Reference**: `spec-phase2-memory-tiers.md` > "Lifecycle Engines: Autonomous Memory Management" > "1. Promotion (L1→L2)"

### Tasks

1.  **Base Engine Interface**
    *   **File**: `src/memory/engines/base_engine.py`
    *   **Requirements**:
        *   [x] Abstract `BaseEngine` class.
        *   [x] Standard methods: `process()`, `health_check()`, `get_metrics()`.
        *   [x] Async/await pattern for non-blocking operations.

2.  **Fact Extractor**
    *   **File**: `src/memory/engines/fact_extractor.py`
    *   **Requirements**:
        *   [x] Use `LLMClient` to process raw text turns.
        *   [x] Implement structured output parsing (JSON/Pydantic) to create `Fact` objects.
        *   [x] **Resilience**: Implement Circuit Breaker pattern (fallback to rule-based extraction on LLM failure).

3.  **Promotion Engine Logic**
    *   **File**: `src/memory/engines/promotion_engine.py`
    *   **Requirements**:
        *   [x] Poll `ActiveContextTier` for recent turns (batch processing).
        *   [x] Invoke `FactExtractor`.
        *   [x] Score facts using existing `CIARScorer`.
        *   [x] Filter based on `promotion_threshold` (default 0.6).
        *   [x] Store qualifying facts in `WorkingMemoryTier`.

---

## Phase 2C: Consolidation Engine (L2 → L3)

**Objective**: Cluster related facts from Working Memory (L2) into coherent Episodes and store them in Episodic Memory (L3).

**Spec Reference**: `spec-phase2-memory-tiers.md` > "Lifecycle Engines: Autonomous Memory Management" > "2. Consolidation (L2→L3)"

### Tasks

1.  **Episode Clustering**
    *   **Logic**: Group facts by time windows (e.g., 24h) and semantic similarity.
    *   **File**: `src/memory/engines/consolidation_engine.py` (or helper module).

2.  **Consolidation Engine Logic**
    *   **File**: `src/memory/engines/consolidation_engine.py`
    *   **Requirements**:
        *   Retrieve facts from `WorkingMemoryTier`.
        *   Use `LLMClient` to generate episode summaries and narratives.
        *   **Dual-Write**: Store `Episode` objects in `EpisodicMemoryTier` (handles both Qdrant and Neo4j storage).
        *   **Resilience**: Handle partial failures (e.g., Vector store success but Graph store failure).

---

## Phase 2D: Distillation Engine (L3 → L4)

**Objective**: Mine patterns and insights from Episodic Memory (L3) to create generalized Knowledge in Semantic Memory (L4).

**Spec Reference**: `spec-phase2-memory-tiers.md` > "Lifecycle Engines: Autonomous Memory Management" > "3. Distillation (L3→L4)"

### Tasks

1.  **Pattern Mining**
    *   **Logic**: Analyze multiple episodes to find recurring themes, user preferences, or rules.
    *   **File**: `src/memory/engines/distillation_engine.py` (or helper module).

2.  **Distillation Engine Logic**
    *   **File**: `src/memory/engines/distillation_engine.py`
    *   **Requirements**:
        *   Query `EpisodicMemoryTier` for relevant episodes.
        *   Use `LLMClient` to synthesize `KnowledgeDocument` objects.
        *   Store in `SemanticMemoryTier` (Typesense).
        *   **Provenance**: Link created Knowledge back to source Episode IDs.

---

## Testing Strategy

For each engine:
1.  **Unit Tests**: Mock `LLMClient` and Storage Tiers to verify logic flow and error handling.
2.  **Integration Tests**: Run with real (test) database instances to verify data persistence.
3.  **Resilience Tests**: Simulate LLM timeouts and storage failures to verify Circuit Breaker and Fallback mechanisms.
