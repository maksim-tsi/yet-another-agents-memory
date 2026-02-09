# Benchmark Automation Documentation

## Overview
This document outlines the automated process for running the "Prospective Memory" benchmark on MAS agents and a naive LLM baseline.

## Prerequisites
- **Python**: 3.10+
- **Poetry**: Installed
- **Docker/Services**: Redis, PostgreSQL, Qdrant, Neo4j, Typesense must be running.
- **Environment**: `.env` file with `GOOGLE_API_KEY`, `POSTGRES_URL`, `REDIS_URL`, etc.

## Configurations
- **[mas_300_run.yml](../configurations/mas_300_run.yml)**: Full 300-question run config.
- **[mas_dry_run_5.yml](../configurations/mas_dry_run_5.yml)**: 5-question dry run config.

## Scripts
### [run_mas_300_benchmark.sh](../../scripts/run_mas_300_benchmark.sh)
This is the main orchestration script.

**Usage:**
```bash
# Run full 300-question benchmark
./scripts/run_mas_300_benchmark.sh

# Run 5-question dry run
./scripts/run_mas_300_benchmark.sh --dry-run
```

**Key Features:**
1. **Pre-flight Checks**:
    - Validates Google Cloud credentials (`test_gemini_flash_lite.py`).
    - Checks infrastructure health (`run_smoke_tests.sh`).
2. **Wrapper Management**:
    - Checks if `mas-full`, `mas-rag`, `mas-full-context` wrappers are running.
    - Starts them if they are not.
3. **Automated Execution**:
    - Runs `run_benchmark.py` sequentially for:
        - `mas-full`
        - `mas-rag`
        - `mas-full-context`
        - `gemini` (Naive LLM)
    - Uses `-y` to skip interactive prompts.
4. **Logging**:
    - Captures run logs to `logs/run_mas_300_benchmark_<timestamp>.log`.

## Artifacts
- **Reports**: Generated in `benchmarks/goodai-ltm-benchmark/data/reports`.
- **Logs**:
    - Wrapper logs: `logs/wrapper_*.log`.
    - Run logs: `logs/run_mas_300_benchmark_*.log`.

## Troubleshooting
- **Wrapper Failures**: Check `logs/wrapper_*.log`.
- **Benchmark Failures**: Check console output or run log.
- **Connectivity**: Run `./scripts/run_smoke_tests.sh -v`.
