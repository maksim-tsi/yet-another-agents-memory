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