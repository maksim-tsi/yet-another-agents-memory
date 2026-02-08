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
