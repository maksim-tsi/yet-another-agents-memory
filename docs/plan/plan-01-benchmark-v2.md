# Implementation Plan: GoodAI-LTM Benchmark v2

**Source Requirements:** `docs/requirements/req-01-benchmark-v2.md`
**Goal:** Transform the CLI tool into a Comparative Evaluation Platform.

## Phase 1: Engine Refactoring (The Runner)

The core of this phase is modernizing `run_benchmark.py` to support complex configurations and isolated execution.

### 1.1 CLI Modernization
*   **Action:** Replace manual `sys.argv` parsing with `argparse`.
*   **New Flags:**
    *   `--agent-override <key>=<value>`: Updates `agent.yaml` dynamically.
    *   `--bench-override <key>=<value>`: Updates `benchmark.yaml` dynamically.
    *   `--compare-with <config_path>`: Optional second agent config for A/B testing.
*   **Validation:** Ensure overrides strictly match the schema of the target configuration.

### 1.2 Execution Isolation (Subprocess Mode)
*   **Action:** Implement `BenchmarkRunner` class that wraps the current main loop.
*   **Mechanism:**
    *   **Dataset Consistency:** Generate the temporary dataset ONCE in the parent process. Pass the *path* to this dataset to both subprocesses to ensure identical tokens/seeds.
    *   For each "match" (Agent A, then Agent B), spawn a distinct OS subprocess utilizing the *same* dataset path.
    *   Pass configuration via temporary YAML files or serialized JSON arguments.
    *   Capture `stdout/stderr` independently to prevent log interleaving.
*   **Constraint:** Ensure the subprocess environment inherits necessary paths but shares no memory state.

### 1.3 Universal Metadata Pipeline
*   **Action:** Update the `AgentInterface` protocol.
*   **Signature Change:** `respond(query: str) -> str` becomes `respond(query: str) -> tuple[str, dict]`.
*   **Safety Layer:** Implement a `MetadataSanitizer` that truncates any metadata payload exceeding 50KB (FR-02.3) before writing to disk.

## Phase 2: Analytics Engine (The Reporter)

This phase focuses on generating the "Vs." report.

### 2.1 Metrics Collection
*   **Action:** Ensure `results.json` structure supports multiple runs.
*   **Schema:** `{ "run_id": "agent_a", "metrics": {...}, "metadata": {...} }`

### 2.2 Comparative Logic (`reporting/comparative.py`)
*   **Action:** Create a `Comparator` class.
*   **Logic:**
    *   Load two `results.json` files (or one merged file).
    *   Calculate Deltas: `(Score_B - Score_A)`, `(Latency_B - Latency_A)`.
    *   Normalize metrics (e.g., scale latency to 0-1 for radar charts if needed).

### 2.3 Visualization
*   **Action:** Generate a static HTML report.
*   **Reasoning:** HTML allows for interactive/collapsible JSON trees for the Metadata (FR-02.1) which static images do not.
*   **Components:**
    *   **Summary Table:** Side-by-side metrics.
    *   **Radar Chart:** SVG/Canvas implementation (avoid heavy plotting libs if possible, or use `files/templates/radar.html`).
    *   **Detail View:** Collapsible accordion for "Reasoning/Metadata" per turn.

## Phase 3: Verification & Integration

### 3.1 Test Suite
*   **Unit:** Test `argparse` overrides logic.
*   **Integration:** Run `benchmark --compare-with agent_b.yaml` on a 5-question mock dataset.

### 3.2 Documentation
*   Update `README.md` with the new CLI usage guide.
*   Create `docs/benchmark-v2-guide.md` explaining how to read the comparative report.
