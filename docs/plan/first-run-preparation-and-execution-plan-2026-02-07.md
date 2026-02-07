# First Run Preparation and Execution Plan (2026-02-07)

**Purpose:** Provide a structured plan for the initial GoodAI LTM benchmark execution with Web UI progress tracking and three-agent comparison (full multi-layer, RAG-only, and full-context baseline).

## 0. Decision Log (2026-02-07)

- The first run prioritizes end-to-end validation over performance baselines.
- Two isolated Poetry environments are mandatory and will not be merged.
- The pre-flight gate uses `scripts/grade_phase5_readiness.sh --mode fast` before any benchmark execution.
- Adapter-level `raise AssertionError("Unreachable")` statements are retained only where they remain inside method bodies to satisfy mypy control-flow analysis; class-level instances were removed to avoid import-time failures.
- Environment activation via `source .venv/bin/activate` is not used; commands must call the absolute venv executable paths on the remote host.

## 0.1 Implementation Tracker

1. Re-run the pre-flight gate after the adapter fixes are validated.
2. Confirm Web UI frontend build assets or use the dev server with API proxy.
3. Start wrapper services for `mas-full`, `mas-rag`, and `mas-full-context` on ports 8080-8082.
4. Execute the single-test configuration and validate run metadata, progress, and logs.
5. Record the run artifacts and proceed to the subset configuration if the single run succeeds.

## 1. Scope and Assumptions

- The run validates end-to-end integration rather than performance baselines.
- Two isolated Poetry environments are required and must remain separate:
  - MAS Memory Layer: repository root.
  - GoodAI LTM Benchmark: benchmarks/goodai-ltm-benchmark/.
- Backend services are expected to be running before execution.
- The remote host requires absolute virtual environment paths.

## 2. Preparation Checklist

### 2.1 Environment Setup (Poetry)

1. **MAS Memory Layer environment**
   - Navigate to the repository root.
   - Run `poetry install --with test,dev`.

2. **GoodAI Benchmark environment**
   - Navigate to benchmarks/goodai-ltm-benchmark/.
   - Run `poetry install`.

### 2.2 Environment Variables

Confirm the following environment variables are available via the repository .env:
- GOOGLE_API_KEY (required for Gemini; do not use GEMINI_API_KEY)
- DATA_NODE_IP, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- NEO4J_USER, NEO4J_PASSWORD

### 2.3 Backend Services

Verify services are reachable and healthy:
- Redis
- PostgreSQL
- Qdrant
- Neo4j
- Typesense

### 2.4 Web UI Build

- Navigate to benchmarks/goodai-ltm-benchmark/webui/frontend.
- Run `npm install` and `npm run build` for production assets.
- If development mode is preferred, run `npm run dev` and rely on the API proxy to port 8005.

## 3. Execution Plan

### 3.1 Start MAS Wrapper Services

Start three wrapper processes (one per agent):
- Full multi-layer agent on port 8080
- RAG-only agent on port 8081
- Full-context baseline on port 8082

### 3.2 Start Web UI Backend

- Run the Web UI backend server at benchmarks/goodai-ltm-benchmark/webui/server.py.
- Confirm the server detects run metadata and exposes API endpoints.

### 3.3 Run Validation Test (Single)

- Execute a single-test configuration to validate the pipeline:
  - benchmarks/goodai-ltm-benchmark/configurations/mas_single_test.yml
- Confirm that:
  - run metadata is created
  - turn_metrics.jsonl is populated
  - Web UI progress endpoints respond

### 3.4 Run Subset Test (Primary First Run)

- Execute the subset configuration for initial evaluation:
  - benchmarks/goodai-ltm-benchmark/configurations/mas_subset_32k.yml
- Run three agent variants in sequence:
  1. mas-full
  2. mas-rag
  3. mas-full-context

## 4. Validation Criteria

1. Wrapper endpoints return healthy status.
2. Runs complete without timeout and write run_meta.json and runstats.json.
3. Web UI displays runs and progress metrics.
4. Logs and result artifacts are persisted under benchmarks/results/.

## 5. Failure Handling

- If a run stalls, inspect run_error.json and turn_metrics.jsonl.
- Validate backend connectivity and memory store health.
- Confirm GOOGLE_API_KEY is present when LLM calls are enabled.

## 6. Post-Run Artifacts

- Results directory: benchmarks/results/goodai_ltm/
- Web UI logs: benchmarks/goodai-ltm-benchmark/webui/logs/
- Wrapper logs: logs/

## 7. References

- Phase 5 readiness checklist: docs/plan/phase5-readiness-checklist-2026-01-02.md
- GoodAI setup: docs/integrations/goodai-benchmark-setup.md
- Web UI backend: benchmarks/goodai-ltm-benchmark/webui/server.py
- Wrapper service: src/evaluation/agent_wrapper.py
- Orchestration script: scripts/run_subset_experiments.sh
