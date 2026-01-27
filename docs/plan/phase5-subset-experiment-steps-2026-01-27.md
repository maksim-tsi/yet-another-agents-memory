# Phase 5 Subset Experiment Execution Specification (32k Baseline)

**Date:** January 27, 2026  
**Scope:** GoodAI LTM Benchmark subset (prospective_memory + restaurant, 32k span)  
**Primary Goal:** Execute the 10% baseline run with deterministic cleanup, reproducible logs, and traceable outputs.

---

## 1. Objective

This document provides a step-by-step execution specification for the Phase 5 subset baseline experiment. It is designed to allow a cold start on the next session without re-deriving the operational steps. The specification prioritizes deterministic startup, serial execution (to avoid quota exhaustion), verified cleanup, and reproducible artifact collection.

---

## 2. Pre-Run Readiness Checklist

1. **Environment**
   - Confirm Python venv exists: `.venv/` at repository root.
   - Confirm GoodAI benchmark venv exists: `benchmarks/.venv-benchmark/`.
   - Confirm required environment variables in `.env`:
     - `REDIS_URL`, `POSTGRES_URL`
     - `GOOGLE_API_KEY` (required for Gemini)
     - Any backend connectivity variables used in test fixtures.

2. **Repository State**
   - Confirm wrapper code and GoodAI model interfaces are present.
   - Confirm subset configuration file exists:
     - `benchmarks/goodai-ltm-benchmark/configurations/mas_subset_32k.yml`.
   - Confirm orchestration and polling utilities exist:
     - `scripts/run_subset_experiments.sh`
     - `scripts/poll_memory_state.py`

3. **Tests**
   - Run wrapper tests before execution:
     - `scripts/run_wrapper_tests.sh` (this is already enforced inside the orchestration script).

---

## 3. Step-by-Step Execution Specification

### Step 1 — Verify wrapper services can start

**Goal:** Ensure all three wrapper services start and pass `/health` within 60 seconds.

**Action:** Start wrappers via the orchestration script (see Step 3). The script performs:
- Wrapper startup on ports 8080/8081/8082
- Health checks with a 60-second timeout

**Expected Outcome:**
- `/health` returns status `ok` for all three wrappers.

---

### Step 2 — Enable memory polling

**Goal:** Record L1/L2/L3/L4 counts per session during benchmark execution.

**Action:** The orchestration script launches `scripts/poll_memory_state.py` for each wrapper, emitting:
- `logs/mas_full_memory_timeline.jsonl`
- `logs/mas_rag_memory_timeline.jsonl`
- `logs/mas_full_context_memory_timeline.jsonl`

**Expected Outcome:**
- Timeline logs are continuously appended and survive wrapper restarts.

---

### Step 3 — Execute subset benchmark runs (serial)

**Goal:** Run GoodAI benchmark sequentially to avoid rate-limit collisions.

**Action:** The orchestration script runs:
- `mas-full`
- `mas-rag`
- `mas-full-context`

Each run uses:
- `benchmarks/goodai-ltm-benchmark/configurations/mas_subset_32k.yml`

**Expected Outcome:**
- GoodAI outputs appear under:
  - `benchmarks/goodai-ltm-benchmark/data/tests/prospective_memory/results/mas-*`
  - `benchmarks/goodai-ltm-benchmark/data/tests/restaurant/results/mas-*`

---

### Step 4 — Verify cleanup between runs

**Goal:** Ensure session state is cleared after each agent run.

**Action:** The orchestration script calls `/sessions` after each run:
- If sessions are non-empty, it calls `/cleanup_force?session_id=all`.
- Cleanup status is logged to:
  - `logs/subset_cleanup_{agent}_YYYYMMDD.log`

**Expected Outcome:**
- Each agent run ends with a clean session list.

---

### Step 5 — Copy results into stable archive

**Goal:** Preserve result artifacts for analysis.

**Action:** The orchestration script copies results into:
- `benchmarks/results/goodai_ltm/subset_baseline_YYYYMMDD/`
- Copies memory timeline logs and cleanup logs into a `logs/` subdirectory.

**Expected Outcome:**
- Timestamped archive exists with per-agent results and operational logs.

---

### Step 6 — Terminate services cleanly

**Goal:** Prevent orphaned wrapper or polling processes.

**Action:** The orchestration script terminates all wrapper and polling PIDs on exit.

**Expected Outcome:**
- No residual wrapper processes remain on ports 8080/8081/8082.

---

## 4. Expected Output Structure

```
benchmarks/results/goodai_ltm/subset_baseline_YYYYMMDD/
├── mas-full/
│   ├── prospective_memory/
│   │   └── results.json
│   └── restaurant/
│       └── results.json
├── mas-rag/
│   └── ...
├── mas-full-context/
│   └── ...
└── logs/
    ├── mas_full_memory_timeline.jsonl
    ├── mas_rag_memory_timeline.jsonl
    ├── mas_full_context_memory_timeline.jsonl
    └── subset_cleanup_*.log
```

---

## 5. Current Readiness Summary (as of 2026-01-27)

**Implemented and Ready:**
- Wrapper services and agent interfaces (full/rag/full_context) with session prefixing.
- Rate limiting, Phoenix tracing separation, and wrapper endpoints (`/run_turn`, `/sessions`, `/memory_state`, `/health`).
- Database isolation mechanisms:
  - PostgreSQL table-level locks for L2 writes.
  - Redis-backed Neo4j lock with auto-renewal.
- Orchestration utilities:
  - `scripts/run_subset_experiments.sh`
  - `scripts/poll_memory_state.py`
- Subset configuration:
  - `benchmarks/goodai-ltm-benchmark/configurations/mas_subset_32k.yml`

**Pending After Subset Execution:**
- Instrumentation module for adapter-level timing (`src/evaluation/instrumentation.py`).
- Subset execution run artifacts and analysis report.

---

## 6. Next Session Starting Point

**Run the subset execution directly via:**
- `scripts/run_subset_experiments.sh`

This script performs all startup checks, launches wrappers, runs the GoodAI subset, verifies cleanup, and archives results.

---

## 7. Notes and Constraints

- Execution should remain serial to protect quota limits.
- Ensure `GOOGLE_API_KEY` is set via `.env`; do not use `GEMINI_API_KEY`.
- Do not use `source .venv/bin/activate` for any scripted execution paths; the orchestration uses explicit paths.

---

## 8. Traceability References

- Wrapper: [src/evaluation/agent_wrapper.py](../../src/evaluation/agent_wrapper.py)
- Orchestration: [scripts/run_subset_experiments.sh](../../scripts/run_subset_experiments.sh)
- Polling: [scripts/poll_memory_state.py](../../scripts/poll_memory_state.py)
- Config: [benchmarks/goodai-ltm-benchmark/configurations/mas_subset_32k.yml](../../benchmarks/goodai-ltm-benchmark/configurations/mas_subset_32k.yml)
- GoodAI interfaces: [benchmarks/goodai-ltm-benchmark/model_interfaces/mas_agents.py](../../benchmarks/goodai-ltm-benchmark/model_interfaces/mas_agents.py)
