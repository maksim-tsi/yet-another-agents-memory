# Promotion Engine Integration Status Report
**Date:** 2026-02-10
**Author:** Antigravity

## Objective
The primary goal was to verify the `FactExtractor` implementation, specifically its ability to extract deferred instructions (e.g., "After responding to X, do Y") and ensure they appear in the agent's `[ACTIVE STANDING ORDERS]`.

## Initial Observation
- **Benchmark Failure:** The Prospective Memory benchmark failed (0/1).
- **Missing Logs:** Despite adding debug logging to `src/memory/engines/fact_extractor.py`, no logs appeared in `logs/wrapper_full.log` during the test run.
- **Silent Failure:** There were no errors indicating the extractor failed; it simply appeared not to run.

## Investigation & Root Cause Analysis

### 1. Verification of Code and Logs
We confirmed that the code on disk contained the debug statements and that the `agent_wrapper` service was restarted. The persistent absence of logs pointed to the code path not being executed at all.

### 2. Tracing the Call Stack
We instrumented `src/agents/memory_agent.py` and `src/memory/engines/promotion_engine.py` with verbose logging to trace the execution flow.
- **Observation:** None of the added logs appeared.
- **Hypothesis:** The `MemoryAgent` was not triggering the promotion cycle.

### 3. Agent Configuration Mismatch
The `MemoryAgent` explicitly checks for `hasattr(self._memory_system, "run_promotion_cycle")`.
- **Discovery:** `src/evaluation/agent_wrapper.py` imports `UnifiedMemorySystem` from the root `memory_system.py` file, not `src.memory.system.py`.
- **Root Cause 1 (Legacy Import):** The wrapper was using a potentially divergent implementation of the memory system.
- **Root Cause 2 (Missing Initialization):** Inspection of `agent_wrapper.py` revealed that while it instantiated `UnifiedMemorySystem`, it **did not instantiate or pass** the `PromotionEngine`, `FactExtractor`, or `TopicSegmenter`. They were defaulting to `None`.
- **Root Cause 3 (Method Mismatch):** `memory_system.py` attempted to call `self.promotion_engine.promote_session`, but the actual `PromotionEngine` class uses the method name `process_session`.

## Corrective Actions

### 1. Fixed Method Call in `memory_system.py`
Updated `run_promotion_cycle` in the root `memory_system.py` to call `process_session` instead of the non-existent `promote_session`.

### 2. Configured Engines in `agent_wrapper.py`
Updated `src/evaluation/agent_wrapper.py` to:
1.  Initialize `LLMClient`.
2.  Instantiate `CIARScorer`, `FactExtractor`, and `TopicSegmenter`.
3.  Instantiate `PromotionEngine` with its dependencies.
4.  Pass the fully configured `PromotionEngine` to the `UnifiedMemorySystem` constructor.

## Next Steps
1.  Restart the `agent_wrapper` service with the corrected configuration.
2.  Re-run the Prospective Memory validation script.
3.  Verify that `FactExtractor` logs now appear.
4.  Proceed with the original task of tuning the `FACT_EXTRACTION_SYSTEM_INSTRUCTION` to properly handle deferred instructions.
