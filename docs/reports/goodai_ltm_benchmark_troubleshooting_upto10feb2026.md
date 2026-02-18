# GoodAI LTM Benchmark Troubleshooting (upto10feb2026)

Consolidated benchmark failure analysis notes and remediation guidance.

Sources:
- benchmark_failure_analysis.md
- benchmark_failure_analysis_2026-02-08.md

---
## Source: benchmark_failure_analysis.md

# Benchmark Failure Analysis: Slowness and Incorrect Answers

## Executive Summary
The `mas-full` benchmark run was halted due to extreme slowness (~17 minutes per question) and a 0/1 accuracy score across all completed questions.
Analysis reveals that the primary cause of slowness is an **Automatic Function Calling (AFC) loop** within the `google-genai` SDK, which defaults to 10 remote calls per turn. The accuracy failure (persistent "Understood" response) is likely a secondary effect of this loop or a prompt conditioning issue.
Contrary to initial suspicions, Qdrant (L3) and Neo4j (L4) were **not** involved, as they are currently mocked/disabled in the `mas-full` configuration.

## Performance Analysis

### Root Cause: Automatic Function Calling (AFC) Loop
The `wrapper_full.log` contains critical evidence of the `google-genai` SDK's internal loop:

```
INFO:src.memory.tiers.working_memory_tier:L2 search found 0 facts for query...
INFO:root:AFC is enabled with max remote calls: 10.
INFO:root:AFC remote call 1 is done.
...
INFO:root:Reached max remote calls for automatic function calling.
```

- **Mechanism**: The SDK detects (or hallucinates) tool usage availability and enters an auto-loop to resolve tool calls.
- **Impact**: It executes the maximum default of **10 sequential LLM calls** for every single user turn.
- **Latency**: Each LLM call (Gemini Flash/Lite) takes 5-10 seconds. 10 calls + overhead results in 100-200 seconds per turn. With the benchmark wrapper's own overhead and potential retries, this balloons to the observed ~17 minutes per question.

### Memory Tier Verification
The user suspected L3 (Qdrant) or L4 (Neo4j) latency. Code analysis confirms these tiers are **disabled** for `mas-full`:
- `src/evaluation/agent_wrapper.py` initializes `UnifiedMemorySystem` with `NullKnowledgeStoreManager`.
- `logs/wrapper_full.log` shows 0 episodes/docs in memory state.
- **Conclusion**: L3/L4 are NOT responsible for the slowness.

## Accuracy Analysis

### The "Understood" Loop
For every completed question, the agent ignored the instruction (e.g., "extract answers") and replied:
> "Understood."

**Failure Reason in Logs**: "The agent did not recite the quote in the correct place." (Generic failure for interaction mismatch).

**Probable Causes**:
1. **Prompt Conditioning**: The benchmark initialization fills the context with informational chunks to which the agent is instructed to reply "Understood". By the time the actual task comes (Question 1), the context window (32k) is filled with this pattern, causing the model to continue it.
2. **AFC Side Effect**: The Automatic Function Calling loop might be consuming the model's "reasoning" steps. If the loop exhausts max calls without a final text output, the SDK might return the last valid text, which could be a generic confirmation or an empty string defaulted to a safe response.

## Recommendations

### 1. Disable Automatic Function Calling (Critical)
Explicitly disable AFC in `src/utils/providers.py` for the `GeminiProvider`:
```python
config_params["automatic_function_calling"] = {"disable": True}
```
This will immediately resolve the 10x latency multiplier.

### 2. Prompt Engineering
Modify `src/agents/memory_agent.py`'s `_build_prompt` to strongly emphasize the **current** user message over the context history.
- Add a "System Instruction" to the API call (supported by Gemini) instead of just the text prompt.
- Append a specific "Answer the user's latest request:" directive at the very end of the prompt.

### 3. Verify Tool Configuration
Investigate why the SDK thinks tools are enabled. If `UNIFIED_TOOLS` are not intended for `mas-full` (which seems to be the case as they are not passed), ensure they are strictly decoupled.

---

## Source: benchmark_failure_analysis_2026-02-08.md

# Benchmark Failure Analysis & Fix Verification Report - 2026-02-08

**Date:** 2026-02-08
**Run ID:** `MAS Mixed 100 Run - 20260208_135704`
**Configuration:** `mas_mixed_100.yml` (13 datasets * 5 examples = 65 tests)

## Executive Summary
This report analyzes the benchmark run following the application of critical fixes for **Automatic Function Calling (AFC)** latency and **TurnData validation** errors.

**The fixes were successful.**
- **Performance**: The benchmark completed in **~23 minutes** (approx. 21s/question), a massive improvement over the previous **>17 minutes/question**.
- **Stability**: 3 out of 4 agents (`mas-full`, `mas-rag`, `gemini`) completed all 65 tests without crashing.
- **Accuracy**: The "Understood" loop (Score 0) persists in some logs, but the system is now operational enough to debug prompt engineering effectively.

## Run Status

| Agent | Status | Completed | Duration | Error |
| :--- | :--- | :--- | :--- | :--- |
| `mas-full` | **SUCCESS** | 65/65 (100%) | 23 min | None |
| `mas-rag` | **SUCCESS** | 65/65 (100%) | 23 min | None |
| `gemini` | **SUCCESS** | 65/65 (100%) | 36 min | None |
| `mas-full-context` | **FAILED** | 19/65 (29%) | N/A | `RuntimeError: Server error 500: Duplicate key value violates unique constraint` |

## Fix Verification

### 1. Latency (AFC Loop)
- **Problem**: `google-genai` SDK was auto-looping 10 times per turn, checking for function calls, causing 17m+ latency per question.
- **Fix**: Disabled `automatic_function_calling` in `GeminiProvider`.
- **Result**: **VERIFIED**. Average turn time dropped to ~5-10 seconds (excluding sleep/overhead). The benchmark is now usable for large-scale testing.

### 2. Validation Error (`TurnData`)
- **Problem**: Large benchmark prompts (due to 32k memory span) exceeded the 10,000 character limit of the `TurnData.content` field in `src/memory/models.py`.
- **Fix**: Increased `max_length` to 200,000.
- **Result**: **VERIFIED**. Agents successfully processed large context prompts without raising `ValidationError`.

### 3. Stale Processes
- **Problem**: Old `agent_wrapper` processes were holding ports and running outdated code.
- **Fix**: Manually terminated processes and verified clean restart.
- **Result**: **VERIFIED**. Wrappers initialized correctly and picked up the new `TurnData` logic.

## Analysis of Failures

### `mas-full-context` Crash
- **Error**:
  ```
  RuntimeError: Failed to call MAS wrapper: Server error 500: {"detail":"Failed to store turn: Insert failed: duplicate key value violates unique constraint \"unique_session_turn\"\nDETAIL:  Key (session_id, turn_id)=(full_context:0e3fd3f4f7b94f67ba4b60c05974739f, 260) already exists."}
  ```
- **Context**: Occurred at test 40/65 (`restaurant` dataset?).
- **Analysis**: The `mas-full-context` agent seems to be retrying or submitting the same turn ID twice in a race condition. Since this agent passes the *entire* history in every turn, it might be triggering a timeout or retry logic in the benchmark runner that leads to a duplicate submission.
- **Action**: Monitor `wrapper_full_context.log` for retry attempts. Requires deeper debugging of the `mas-full-context` session management.

### Accuracy ("Understood" Loop)
- **Observation**: Despite the fixes, the agents often respond with "Understood." or JSON when text is expected (or vice-versa).
- **Example (`gemini`)**:
  - Test: "Append a quote..."
  - Response: "Understood."
  - Result: Score 0/1.
- **Analysis**: This confirms the secondary hypothesis that the benchmark's "filler" tasks (trivia conditioning) are causing the model to overfit to the "Understood" response pattern.
- **Action**: Prompt engineering is still required. The system is now fast enough to iterate on this rapidly.

## Recommendations
1.  **Investigate `mas-full-context`**: Debug the duplicate key error. It might need a database transaction fix or a client-side retry fix.
2.  **Iterate on Prompts**: Modify `MemoryAgent` and `GeminiProvider` to break the "Understood" pattern.
3.  **Proceed to Analysis**: Now that `mas-full` runs successfully, we can analyze the *content* of its memories (L1/L2) to see if it's actually using the memory system.

