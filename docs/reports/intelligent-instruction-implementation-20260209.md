# Intelligent Instruction Handling - Progress Report
**Date:** 2026-02-09
**Feature:** Active Standing Orders & Instruction Handling

## Overview
This report documents the implementation and debugging of the "Intelligent Instruction Handling" feature for the MAS Memory Layer. The objective is to enable the agent to intelligently handle delayed instructions and conditional tasks (e.g., "In 2 turns, say 'Bingo'") by treating them as Active Standing Orders.

## Implementation Details

### 1. Schema Changes
- **`FactType.INSTRUCTION`**: Added to `src/memory/models.py`.
- **Extraction Schema**: Updated `FACT_EXTRACTION_SCHEMA` and `FACT_EXTRACTION_SYSTEM_INSTRUCTION` to extract conditional/delayed commands as `instruction`.

### 2. Memory Agent Updates
- **Session State Injection**: Modified `MemoryAgent._build_prompt` to inject `[SESSION STATE]` containing:
    - Current Turn Number (calculated from state).
    - Current Time.
- **Active Standing Orders**: Injected `[ACTIVE STANDING ORDERS]` section populated by `FactType.INSTRUCTION` facts retrieved from memory.
- **Format Guardian**: Added explicit instructions to prioritize user-requested formats (e.g., JSON) while still executing instructions.

## Validation & Debugging

### Validation Run 1: Full Scope (10 Questions) -> **FAILED**
- **Error**: `google.genai.errors.ServerError: 503 UNAVAILABLE`.
- **Root Cause**: Gemini API instability during high load/concurrency.
- **Action**: Reduced validation scope to 1 question/example for debugging.

### Validation Run 2: Reduced Scope -> **FAILED (Instruction Ignored)**
- **Observation**: Agent failed to execute "append quote to 5th response".
- **Investigation**:
    - **Issue 1: Broken Turn Counting**: `Current Turn: 0` appeared repeatedly in logs. The agent logic (`len(self.history)`) was flawed because `history` wasn't persisting correctly in the stateless `MemoryAgent`.
        *   **Fix**: Modified `_reason_node` to pass `turn_id` from `AgentState` directly to `_build_prompt`.
    - **Issue 2: Scrambled Context**: `## Recent Conversation` displayed turns in **reverse chronological order** (Newest -> Oldest).
        *   **Impact**: The LLM saw: `3. USER... 2. ASSISTANT... 1. USER...`. This completely broke temporal reasoning ("in 2 turns") because the "future" (recent) turns appeared *before* the instruction in the prompt's linear flow.
        *   **Fix**: Reversed the `recent_turns` list in `_format_recent_turns` to present history Chronologically (Oldest -> Newest).

### Validation Run 3: Fixed Context & Turn Counting -> **FAILED (Constraint Conflict)**
- **Observation**: Despite correct turn counting and chronological context, the agent *still* failed to append the quote.
- **Root Cause Analysis (Post-Mortem)**:
    - **Constraint Conflict**: The user prompt strictly requested a JSON format (`["answer"]`).
    - **Priority Mismatch**: Even with the "Format Guardian" instruction, the model prioritized the `System Instruction` to "output valid JSON" over the "Active Standing Order" to append text.
    - **Log Evidence**: The agent output `["Cyprus"]` (correct JSON) but essentially "forgot" or "suppressed" the instruction to avoid breaking the JSON format.
    - **Conclusion**: The current prompt engineering strategy for "Format Guardian" is insufficient against strong system-level format constraints.

## Current Status
- **Codebase**: Fully implemented.
- **Verified Fixes**: Turn Counting, Context Ordering.
- **Unresolved Issue**: Strong format constraints (JSON) overriding prospective memory instructions.
- **Recommendation**: Needs a robust "Output Parser" or a multi-stage reasoning step where the agent explicitly "plans" the instruction execution *before* formatting the final output.

## Artifacts
- **Task List**: `task.md` updated.
- **Implementation Plan**: `implementation_plan.md` updated.
- **Logs**: Debug logs enabled (`logging.DEBUG`) in `agent_wrapper.py`.
