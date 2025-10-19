
### **Detailed Implementation Plan: Multi-Agent Memory Benchmark Evaluation**

**Overall Objective:** To execute a rigorous, quantitative evaluation of our Hybrid Memory Architecture using the GoodAI LTM Benchmark, generating the empirical results required to satisfy reviewer feedback for the AIMS 2025 paper.

**Project Management:** We will track this plan using a simple project board (e.g., GitHub Projects, Trello) with columns for **To Do**, **In Progress**, and **Done**. Each numbered task below represents a card on that board.

---

### **Phase 0: Foundation & Infrastructure Setup (1-2 Days)**

**Goal:** To establish a stable, fully-deployed, and ready-to-use development and execution environment.

*   **Task 0.1: Deploy Asymmetric Infrastructure**
    *   **Action:** On the two P320S machines (`orchestrator-node` and `data-node`), deploy the final `docker-compose.yml` files as specified in the DevOps-approved plan.
    *   **Deliverable:** All services (Redis, Postgres, n8n, Qdrant, Neo4j, Typesense) are running and accessible over the network.

*   **Task 0.2: Set Up Project Repository & Environment**
    *   **Action:** Clone the `mas-memory-layer` repository onto the `orchestrator-node`. Create a Python 3.13 virtual environment and install all dependencies from `requirements.txt`.
    *   **Deliverable:** A ready-to-code project environment on the `orchestrator-node`.

*   **Task 0.3: Configure API Keys and Secrets**
    *   **Action:** Create a `.env` file in the root of the repository on the `orchestrator-node`. Populate it with the necessary API keys for the LLMs (Mistral, Anthropic), databases, and any other services.
    *   **Deliverable:** A populated `.env` file that is correctly ignored by Git.

*   **Task 0.4: Set Up the GoodAI LTM Benchmark**
    *   **Action:** On the `orchestrator-node`, clone the official `goodai-ltm-benchmark` repository into a separate directory. Install its dependencies in its own virtual environment.
    *   **Deliverable:** The benchmark's `run_benchmark.py` script is executable.

### **Phase 1: Agent and Baseline Implementation (3-4 Days)**

**Goal:** To implement the Python classes for our three experimental configurations: the full system and the two baselines.

*   **Task 1.1: Implement the "Full System" Agent (`FullSystemAgent`)**
    *   **Action:** Create a new `agents/` directory. Inside, build the `FullSystemAgent` class. This class will use LangGraph to orchestrate the full `PERCEIVE -> RETRIEVE -> REASON -> UPDATE_MEMORY -> RESPOND` cycle, as detailed in the benchmark implementation guide. It will be initialized with an instance of our `UnifiedMemorySystem`.
    *   **Deliverable:** A Python class `FullSystemAgent` that can be instantiated and can process a single conversational turn.

*   **Task 1.2: Implement the "Standard RAG" Baseline (`StandardRAGAgent`)**
    *   **Action:** In the `agents/` directory, create the `StandardRAGAgent` class. This agent's logic will be simple: on each call, it takes the user message, queries a single Qdrant collection containing the entire history, and feeds the results to an LLM. It will be stateless.
    *   **Deliverable:** A Python class `StandardRAGAgent` that implements the logic from UC-02.

*   **Task 1.3: Implement the "Full-Context" Baseline (`FullContextAgent`)**
    *   **Action:** In the `agents/` directory, create the `FullContextAgent` class. This agent will be the simplest: it will maintain the conversation history in a list, and for every call, it will append the entire history to the prompt sent to the LLM.
    *   **Deliverable:** A Python class `FullContextAgent` that implements the logic from UC-03.

### **Phase 2: Integration, Tooling, and Validation (2-3 Days)**

**Goal:** To connect our implemented agents to the benchmark runner and ensure the entire data pipeline is working correctly.

*   **Task 2.1: Implement the `AgentWrapper` API**
    *   **Action:** Create a simple web server (e.g., using Flask or FastAPI) that exposes the `/run_turn` endpoint. This wrapper will be configurable to instantiate one of the three agent classes from Phase 1 based on a command-line argument or environment variable.
    *   **Deliverable:** A running web service that the GoodAI benchmark can call.

*   **Task 2.2: Implement Robust Instrumentation**
    *   **Action:** Integrate structured logging into the `UnifiedMemorySystem` and the `AgentWrapper`. For every turn, we must capture the key metrics defined in the evaluation protocol (latency, token counts, cache hits, etc.) and write them to a structured log file (e.g., JSONL).
    *   **Deliverable:** A logging utility that produces auditable, machine-parsable logs for each experimental run.

*   **Task 2.3: Perform an End-to-End Dry Run**
    *   **Action:** Manually run a single, short test from the GoodAI benchmark (e.g., a simple recall test) against one configuration (e.g., `FullSystemAgent` with Mistral).
    *   **Deliverable:** A verified, successful run that confirms all components are communicating correctly: Benchmark Runner -> Agent Wrapper -> Agent -> UnifiedMemorySystem -> Redis/Qdrant -> Logger.

### **Phase 3: Benchmark Execution & Data Collection (2-4 Days, mostly unattended)**

**Goal:** To systematically execute all 12 planned experimental runs and collect the raw data.

*   **Task 3.1: Create the Execution Script (`run_experiments.sh`)**
    *   **Action:** Write a shell script that automates the entire evaluation. This script will loop through the models (`mistral`, `claude`), the memory spans (`32k`, `200k`), and our agent configurations (`full`, `rag`, `full_context`), starting the `AgentWrapper` with the correct settings and then calling the benchmark's `run_benchmark.py` script.
    *   **Deliverable:** A single script that can run all 12 experiments unattended.

*   **Task 3.2: Execute the Full Benchmark Suite**
    *   **Action:** Run the `run_experiments.sh` script. This will be a long-running process. Monitor the `orchestrator-node` using `htop` and `docker stats` to ensure stability.
    *   **Deliverable:** A complete set of raw output files for all 12 runs.

*   **Task 3.3: Organize and Archive Raw Data**
    *   **Action:** Create a structured `results/` directory. For each of the 12 runs, archive the generated HTML report from the benchmark and our own detailed instrumentation logs into a clearly named subdirectory (e.g., `results/mistral_32k_full_system/`).
    *   **Deliverable:** A clean, well-organized archive of all raw experimental data.

### **Phase 4: Analysis, Reporting, and Paper Revision (2-3 Days)**

**Goal:** To analyze the collected data, generate the final result tables, and revise the research paper.

*   **Task 4.1: Develop the Analysis Script (`analyze_results.ipynb`)**
    *   **Action:** Create a Jupyter Notebook that programmatically parses the raw data from the `results/` directory.
    *   **Deliverable:** A notebook that can ingest all the data and perform the necessary calculations.

*   **Task 4.2: Generate Final Result Tables**
    *   **Action:** Use the analysis notebook to generate the two key tables for our paper: "Functional Correctness (GoodAI LTM Scores)" and "Operational Efficiency (Latency, Token Cost, etc.)."
    *   **Deliverable:** The final, formatted Markdown tables ready to be inserted into the paper.

*   **Task 4.3: Revise and Finalize the AIMS 2025 Paper**
    *   **Action:** Perform the full revision of the paper as planned, replacing the qualitative scenario with our new quantitative results and incorporating all other feedback.
    *   **Deliverable:** The final, submission-ready PDF of our revised research paper.