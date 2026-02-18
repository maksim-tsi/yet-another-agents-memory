# Benchmark v2 and Headless Pivot (version-0.9)

Consolidated benchmark v2 implementation plan and headless pivot directive.

Sources:

---

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

---


Here is the **High-Level Directive**. It focuses on "Intent" rather than just file paths, allowing the developer to hunt down the dependencies and references intelligently.

---

# Task: Deprecate and Remove Benchmark UI ("Headless Pivot")

**Context:**
We are shifting the architecture to a "Two-Container Microservices" model. In this model, the Benchmark is a headless runner (the "Judge") that communicates with the Agent via HTTP. The "Memory Inspector" UI (Component 2 of ADR-008) has proven to be unnecessary technical debt (10k+ files in `node_modules`) and is being revoked.

**Objective:**
Purge the frontend/UI components from the repository and update the architectural documentation to reflect this "Headless" strategy.

## Step 1: Architectural Record Update (ADR-008)

* **Action:** Modify `docs/ADR/008-adoption-of-goodai-benchmark.md`.
* **Change:** Do NOT delete the file. Instead, append a **"Status Update - [Date]"** section at the bottom (or update the Status to "Amended").
* **Content:** Record that **"Component 2: MAS Memory Inspector (Visualizer)"** has been **Revoked**. State that we are opting for a "Headless Telemetry" approach where logs/metrics are emitted to standard collectors (TypeSense/Phoenix) instead of a custom React frontend.

## Step 2: Codebase Purge

* **Action:** Identify and delete the directory `benchmarks/goodai-ltm-benchmark/webui/`.
* **Cleanup:**
* Scan `pyproject.toml` (in the benchmark folder) for web-server dependencies that were *only* used for the UI (e.g., `flask`, `browser-cookie3` if unused elsewhere). Remove them if they are orphans.
* Check `runner/` scripts. If there is a `run_web_server.py` or similar, delete it. Keep only the CLI/Headless runners (`run_benchmark.py`).



## Step 3: Documentation Sanitization

* **Action:** Scan `README.md`, `docs/dev-quickstart.md`, and `DEVLOG.md`.
* **Change:** Remove all instructions related to:
* Installing Node.js/NPM/Yarn.
* "Starting the Dashboard".
* Accessing `localhost:3000`.


* **Goal:** The new "Quickstart" should end at "Run the benchmark script."

---

**Definition of Done:**

1. The repo size drops significantly (removal of `node_modules`).
2. `ADR-008` clearly reflects the decision to drop the UI.
3. A developer following `README.md` is never asked to install Javascript tools.

