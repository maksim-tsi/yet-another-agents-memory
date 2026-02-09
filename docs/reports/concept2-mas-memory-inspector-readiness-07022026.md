This document captures the "Black Box" discovery we performed on February 07 2026 and serves as the **technical specification for the Refactoring Phase** that must happen *before* we can build the Inspector UI.

---

# Readiness Analysis: Concept 2 (MAS Memory Inspector)

**Date:** February 07, 2026
**Target:** AIMS'25 Paper Validation (Cognitive Telemetry)
**Status:** 🔴 **Blocked by Architectural Gaps**

## 1. Executive Summary

The current codebase (`v1.0.0`) implements the *mechanisms* of the AIMS'25 architecture (Promotion, CIAR Scoring) but fails to expose the *reasoning* behind them. The system operates as a "Black Box," making it impossible to visualize the "Why" behind memory promotions in the proposed Inspector UI.

**Conclusion:** We cannot proceed directly to Concept 2 implementation. A **Prerequisites Refactoring Phase** is required to capture cognitive data that is currently being discarded or never generated.

---

## 2. Gap Analysis: The "Invisible Brain" Problem

### Gap 2.1: Discarded LLM Reasoning (`FactExtractor`)

* **Current State:** The `_extract_with_llm` method requests specific fields (`content`, `impact`, `certainty`) from the LLM via `FACT_EXTRACTION_SCHEMA`.
* **The Issue:** The LLM likely generates internal reasoning to determine the `impact` score, but the schema does not request it, and the code does not capture it.
* **Impact on Concept 2:** The Inspector UI will display "Impact: 0.9", but when the user asks "Why?", the system will be silent. This weakens the "Explainable AI" claim of the paper.

### Gap 2.2: Arithmetic Scoring without Semantics (`CIARScorer`)

* **Current State:** `CIARScorer.calculate()` is a purely deterministic function: `(Certainty * Impact) * Decay`.
* **The Issue:** The scorer cannot explain *why* a fact received a specific Impact score (e.g., "Matches 'Business Preference' heuristic").
* **Impact on Concept 2:** The "Significance Formula" view will be mathematically correct but semantically empty.

### Gap 2.3: Silent Decision Logic (`PromotionEngine`)

* **Current State:** Critical cognitive decisions (Promote vs. Ignore) happen inside `if` statements (e.g., `if segment_score < threshold: continue`).
* **The Issue:** These decisions are only visible if `DEBUG` logs are enabled and tailed via SSH. There is no structured event stream.
* **Impact on Concept 2:** The UI cannot animate the "Promotion Flow" because it never receives the "Decision Made" signal.

---

## 3. Prerequisites Recommendation (Refactoring Plan)

To unblock Concept 2, the following engineering tasks must be completed first.

### Task P-1: Schema Enrichment (The "Reasoning" Field)

We must update the domain models to strictly enforce the capture of explanations.

* **Target File:** `src/memory/models.py`
* **Change:**
```python
class Fact(BaseModel):
    # ... existing fields ...
    # NEW FIELD
    justification: str | None = Field(
        default=None,
        description="LLM-generated reasoning or Heuristic Rule ID explaining the impact score."
    )

```


* **Target File:** `src/memory/engines/topic_segmenter.py`
* **Change:** Add `reasoning: str` to the `TopicSegment` model.

### Task P-2: Prompt Engineering for Explainability

We must force the LLM to "think out loud" in its JSON output.

* **Target File:** `src/memory/schemas/fact_extraction.py`
* **Change:** Update `FACT_EXTRACTION_SCHEMA` to require a `justification` field for every extracted fact.
* *Prompt Tweak:* "For every fact, strictly provide a 1-sentence justification explaining why it is significant enough for long-term storage."



### Task P-3: Telemetry Infrastructure (The "Nervous System")

We need a standard way to transmit "Thoughts" from the backend to the frontend.

* **Target File:** `src/common/telemetry.py` (New File)
* **Change:** Implement a lightweight `AsyncCognitiveMonitor`.
```python
class CognitiveEvent(BaseModel):
    event_type: Literal["PROMOTION", "RETRIEVAL", "FILTER_REJECT"]
    component: str  # e.g., "PromotionEngine"
    details: dict[str, Any]
    timestamp: float

# Singleton Async Queue
TELEMETRY_QUEUE: asyncio.Queue[CognitiveEvent] = asyncio.Queue()

```



---

## 4. Modified Implementation Roadmap

1. **Phase 1: Refactoring (Prerequisites)**
* Update Pydantic Models (`Fact`, `TopicSegment`).
* Update LLM Prompts (`FactExtractor`).
* Create `Telemetry` module.


2. **Phase 2: Instrumentation (Concept 2 Backend)**
* Inject `TELEMETRY_QUEUE.put()` calls into `PromotionEngine` and `CIARScorer`.


3. **Phase 3: Visualization (Concept 2 Frontend)**
* Build the WebSocket consumer in FastAPI.
* Build the React Inspector UI.
