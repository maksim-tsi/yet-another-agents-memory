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
