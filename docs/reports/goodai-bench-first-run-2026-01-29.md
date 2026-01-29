# GoodAI LTM Benchmark — First Subset Run Analysis
Date: 2026-01-29

## Executive Summary ✅
- The logs show **no evidence of a continuous 9-hour active benchmark run** processing turns. The researcher manually interrupted the process after ~9 hours, but recorded evidence indicates the system was largely idle (health checks and sparse rate-limiter entries) rather than actively processing benchmark turns.
- Completed/validated runs include:
  - **MAS Subset - 32k**: 17 events, 7,267 total tokens, **4.0 s duration** (source: `benchmarks/.../MAS Subset - 32k/runstats.json`)
  - **MAS Single Test - Verification**: ≈50 events, **~9.49 s duration**, per-run tests (Prospective Memory scored 0/1)
- Primary shortcomings: **no real-time progress visibility**, **no per-turn timing instrumentation**, and **L2-L4 memory tiers remained unpopulated** during the completed run.

---

## Key Findings

### Run-level summary
| Run Name | Events | Total Tokens | Duration (s) | Average time / event (s) | Notes |
|---|---:|---:|---:|---:|---|
| MAS Subset - 32k | 17 | 7,267 | 4.0 | 0.24 | Completed (short)
| MAS Single Test - Verification | ~50 | 7,267* | 9.49 | 0.19 | Completed; Prospective Memory test failed (0/1)

*Tokens for MAS Single Test vary across test artifacts; some per-test JSONs show larger token counts for other tests.


### Log surface indicators
- `logs/wrapper_*.log` — ≈3,280 lines each, predominantly health-check GETs (`GET /sessions`) and server startup messages; very few actual processing requests observed.
- `logs/rate_limiter_full_*.jsonl` — **~20–30 entries across 12 files** spanning Jan 27–28, 2026; **sparse** token estimates and short activity bursts (most active window: 4 calls in ~3s at 2026-01-28T19:35).
- `benchmarks/.../MAS Subset - 32k/master_log.jsonl` — 17 events; timestamps indicate start ~2026-01-28T19:35 and termination ~2026-01-28T19:48; the run did not continue for long.
- `logs/mas_full_memory_timeline.jsonl` — L1 activity present (e.g., `l1_turns: 6`), **L2/L3/L4 counts remained 0** for many sessions.

---

## Timing Analysis
> Note: The repository currently lacks per-operation timing instrumentation (LLM call durations, per-storage operation durations) at the turn level. Timing below uses available run durations and master_log event counts; this provides approximate means but not a precise breakdown.

- **MAS Subset - 32k**: 4.0 s / 17 events ≈ **0.24 s per event (mean)**
- **MAS Single Test** (approx): 9.49 s / 50 events ≈ **0.19 s per event (mean)**

### Component-level distribution (estimates & limitations)
- The logs do not provide reliable per-component timings. Rate-limiter logs show `delay_applied` values (commonly 0.6s) for a few calls, but calls are sparse. The dominant *observed* time budget during the interruption period was **idle/waiting** (health checks), not LLM latency or memory processing. Therefore: **we cannot compute an accurate per-component time split** without additional instrumentation.

---

## Issues Identified
1. **No real-time progress visibility** for long runs — the researcher could not tell whether the run was processing or stuck.
2. **L2–L4 remained unpopulated** during the run; promotion/consolidation engines did not trigger (or did not record) in the observed sessions.
3. **Insufficient per-turn instrumentation** — no timing breakdown for LLM calls vs storage vs orchestration.
4. **OpenTelemetry warning** appears on startup: `Overriding of current TracerProvider is not allowed` (cosmetic but should be cleaned up).
5. **Historical vendor data not to be used** — a June 2024 run exists from GoodAI but differs from our current benchmark (we do not include vendor runs in our analysis).
6. **AgentRouter 401s** (historical) — unrelated to subset run, but present in older logs.

---

## Recommendations (short)
- Add **real-time progress reporting** (use `tqdm` progress bars for CLI experiments). Do not implement changes yet; see Phase 5 plan (below) for details.
- Add **per-turn timing instrumentation** (wrap LLM calls and storage operations with timers and record JSONL per-turn metrics).
- Add **stuck-run detection** (default threshold: 15 minutes; configurable via `--stuck-timeout` or `MAS_BENCH_STUCK_TIMEOUT_MINUTES`).
- Surface storage adapter metrics in run summaries (p50/p95) and append to `runstats.json`.

---

## Appendix A — Storage benchmark (summary from `benchmarks/results/all_results.json`)
| Adapter | Avg Latency (ms) | P95 (ms) | Notes |
|---|---:|---:|---|
| Redis (L1) | 0.30 | 0.34 | Sub-millisecond responses
| Redis (L2) | 0.31 | 0.40 | Stable
| Qdrant | 6.84 | 8.86 | Typical vector DB latency
| Neo4j | 4.25 | 8.14 | Some store failures observed earlier
| Typesense | 14.83 | 31.74 | Highest search latency

---

## Appendix B — Partial / Incomplete Runs (included for transparency)
- The 9-hour interruption by the researcher is **not supported by logs as an active processing window**. Evidence indicates the process was mostly idle and returned health-check responses during the 9-hour period.
- A June 2024 vendor run (Benchmark 3 - 32k) exists but **is excluded** from our primary analysis by directive.

---

## Decisions Log (Agreed items)
- Use `tqdm` for progress reporting (lightweight, headless-friendly).
- Default stuck timeout: **15 minutes**, configurable via `--stuck-timeout` and env var `MAS_BENCH_STUCK_TIMEOUT_MINUTES`.
- CLI verbosity flags: support `--verbose` (detailed per-turn logs) and `--quiet` (errors-only); respect `LOG_LEVEL` env var as fallback.
- We will **document** required runner visibility upgrades in a Phase 5 plan but **will not** implement changes in this ticket.

---

## Artifacts and Sources
- `benchmarks/goodai-ltm-benchmark/tests/MAS Subset - 32k/runstats.json`
- `benchmarks/goodai-ltm-benchmark/tests/MAS Subset - 32k/master_log.jsonl`
- `benchmarks/goodai-ltm-benchmark/tests/MAS Single Test - Verification/master_log.jsonl`
- `logs/rate_limiter_full_*.jsonl`
- `logs/wrapper_*.log`
- `logs/mas_full_memory_timeline.jsonl`


---

If you want, I can now:
1) Add a short verification script that extracts per-run summaries for easier human inspection; or
2) Proceed to create the Phase 5 plan file documenting the implementation approach (I've created it alongside this report).

(Per your instruction, I did not modify any runner code or add instrumentation — only documented the plan for future implementation.)
