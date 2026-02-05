# Visibility Improvement Plan for the MAS-Integrated GoodAI LTM Benchmark

## 1. Objectives
The goal is to provide transparent, headless-friendly observability for long-running benchmark executions while preserving the original GoodAI benchmark datasets and evaluation procedures.

## 2. Non-Goals
- Altering benchmark datasets, question prompts, or scoring logic.
- Modifying the GoodAI evaluation methodology.
- Replacing the existing HTML report generation pipeline.

## 3. Proposed Enhancements

### 3.1 Headless Progress Reporting
Implement a CLI progress indicator using `tqdm` within the scheduler to provide real-time progress, including:
- Current test name and index
- Token count and elapsed time
- Estimated completion ratio

### 3.2 Per-Turn JSONL Metrics
Introduce a `turn_metrics.jsonl` output generated alongside `runstats.json` and `master_log.jsonl`. Each record should contain:
- `timestamp`
- `test_id`
- `turn_id`
- `llm_ms`
- `storage_ms`
- `total_ms`
- `tokens_in`
- `tokens_out`
- `status` (success/error)

This format enables ingestion by Grafana’s JSON data source plugin.

### 3.3 Stalled-Run Watchdog
Add a watchdog that triggers after a configurable inactivity threshold (default 15 minutes). Upon activation it should:
- Emit a console warning
- Write a `run_error.json` diagnostic file
- Preserve the most recent progress snapshot

### 3.4 Grafana Dashboard (JSON Plugin)
Provide a dashboard template that reads the JSONL output and presents:
- Progress over time (completed turns/tests)
- Latency distributions (p50/p95/p99)
- Token throughput
- Stall events and error markers

### 3.5 Phoenix Trace Alignment
Ensure Phoenix/OpenTelemetry initialization occurs once per process to avoid `TracerProvider` override warnings and preserve LLM trace continuity.

## 4. Implementation Phases

**Phase 1: Diagnostic Instrumentation**
- Implement `tqdm` progress reporting
- Emit `turn_metrics.jsonl`
- Add watchdog with `run_error.json`

**Phase 2: Dashboard Enablement**
- Add Grafana JSON dashboard template
- Document ingestion instructions in the benchmark README

**Phase 3: Trace Stabilization**
- Refactor Phoenix initialization to ensure single-provider use

## 5. Validation Criteria
- Headless runs show CLI progress output throughout execution.
- `turn_metrics.jsonl` includes per-turn records for at least 95% of turns.
- Watchdog triggers and writes `run_error.json` when the run stalls.
- Grafana dashboard renders metrics without manual data transformation.
