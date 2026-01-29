# Phase 5 — Post-Subset Run: Visibility & Reliability Improvements
Date: 2026-01-29

## Purpose
Document the agreed plan and decisions to improve visibility, progress reporting, and stuck-run detection for Phase 5 of the GoodAI LTM benchmark work. This is a planning artifact only; no runner or functional changes will be applied in this ticket.

## Problem Statement
During the first subset run, a researcher manually interrupted the job after ~9 hours because there was no clear progress visibility; logs showed health checks and minimal activity rather than ongoing processing. Without actionable visibility and stuck-run detection, researchers cannot determine whether the system is processing or stuck.

## Goals
- Provide real-time progress feedback during benchmark runs (CLI-friendly, headless-safe).
- Record per-turn timing data (LLM call duration, memory operation duration, orchestration time).
- Detect and alert on stuck runs (configurable threshold), providing diagnostics and optional automated cleanup.
- Keep instrumentation lightweight and opt-in for runs that need high visibility.

## Agreed Decisions
- Progress reporting library: **tqdm** (lightweight, headless-friendly). ✅
- Default stuck timeout: **15 minutes** (configurable via `--stuck-timeout` or env `MAS_BENCH_STUCK_TIMEOUT_MINUTES`). ✅
- CLI verbosity: support `--verbose` (detailed per-turn logging) and `--quiet` (errors-only); respect `LOG_LEVEL` env var as fallback. ✅
- Per-turn metrics: record JSONL `turn_metrics` lines with fields such as: `timestamp`, `session_id`, `turn_index`, `llm_ms`, `storage_ms`, `tokens_in`, `tokens_out`, `status`.
- Run termination behavior: upon stuck timeout, write a `run_error.json` summarizing last known state and optionally raise an alert (implementation subject to infra decisions).

## Implementation Outline (high-level)
> NOTE: This file is a plan only. Do not modify runner code as part of this ticket.

1. **CLI Changes**
   - Add `--stuck-timeout MINUTES` and `--progress [tqdm|none]` flags to `run_benchmarks.py`/runner CLI.
   - Implement `--verbose` and `--quiet` flags. CLI overrides `LOG_LEVEL` env var.

2. **Progress UX**
   - Add `tqdm` progress bar for overall test progress and nested bars for batch processing where applicable.
   - Use `tqdm.write()` for log lines to avoid progress UI corruption.

3. **Per-turn Instrumentation**
   - Wrap LLM calls (the central `ask_gemini` or equivalent interface) with a timer and log `llm_ms`.
   - Wrap memory adapter calls (L1/L2/L3/L4 interactions) with timers and log `storage_ms` per adapter.
   - Emit a `turn_metrics.jsonl` entry per turn with fields: `timestamp`, `session_id`, `turn_id`, `role`, `llm_ms`, `storage_ms`, `tokens_in`, `tokens_out`, `error`.

4. **Stuck Detection & Alerts**
   - A background monitor checks `last_event_timestamp` and compares with `--stuck-timeout`.
   - On timeout, persist `run_error.json` (diagnostics) and optionally attempt to stop the run gracefully.

5. **Run Summary**
   - Extend `runstats.json` to include `turn_metrics_summary` with p50/p95/p99 for `llm_ms` and `storage_ms` and total `turns` and `events`.

## Verification Criteria
- Developer and researcher can run a subset and see `tqdm` progress output on the console (or no UI in `--progress none` mode).
- `turn_metrics.jsonl` contains per-turn timing for at least 95% of turns in a test run.
- A simulated stuck-run (pause processing for > 15 minutes) triggers `run_error.json` and writes diagnostic info.
- `runstats.json` includes the new summary fields.

## Rollout Plan & Prioritization
- Phase 5.1 (Design & Tests): Implement per-turn timers as instrumentation-only (non-invasive), add unit tests for metric emission.
- Phase 5.2 (CLI UX): Integrate `tqdm` progress bars, CLI flags, and documentation updates.
- Phase 5.3 (Diagnostics): Implement stuck detection, `run_error.json`, and run-summary enhancements.

## Risks & Mitigations
- **Overhead:** Instrumentation may add small overhead. Mitigation: Make per-turn timing optional behind `--verbose` and set sampling defaults.
- **Log Volume:** `turn_metrics.jsonl` can be large; mitigation: compress/rotate logs and provide sampling options.

## Owners & Next Steps
- Owner: Benchmark engineering lead (please assign)
- Next step: Create a small spike PR that adds per-turn timers with tests and a README example (no changes performed in this task).

---

*This document captures decisions agreed during analysis and planning (2026-01-29). Implementation is to be performed in a subsequent development task.*
