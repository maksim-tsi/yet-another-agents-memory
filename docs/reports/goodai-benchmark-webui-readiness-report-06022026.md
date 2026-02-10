> WARNING (DEPRECATED, 2026-02-10)
> This document describes a component (WebUI) that has been removed from the architecture.
> It is preserved here for historical context only.

## Readiness Verdict
**MVP‑ready for local use**, not yet production‑ready.  
You can launch runs, view progress/logs, and choose LLM/agent/scope, but there are several reliability and correctness gaps that will show up with repeated runs or multiple users.

---

## What’s Working (✅)
- **Backend API exists**: `/api/presets`, `/api/runs`, `/api/runs/{id}/progress`, `/api/runs/{id}/logs`.
- **Run launch pipeline**: spawns `runner/run_benchmark.py` with the new flags.
- **Progress ingestion**: reads `turn_metrics.jsonl` + `runstats.json`.
- **Logs browser**: lists artifacts and tails any file.
- **Setup UI**: LLM preset + agent + benchmark config + single test filter + stuck timeout.
- **Indexing helper**: can compute question counts per config.
- **Local dev**: Vite dev server w/ API proxy to FastAPI.

---

## Gaps / Risks (⚠️)

### 1) **Run directory collisions**
`start_run()` uses:
```py
run_dir = make_run_path(run_name or "Run", agent_name)
```
If you launch multiple runs with the same `run_name`+`agent_name`, logs and artifacts **overwrite each other**.  
**Impact:** High (data loss / ambiguous run results).

### 2) **`run_id` vs `run_name` mismatch**
We **store run meta by `run_id`**, but the directory naming is based on `run_name`.  
**Impact:** Medium (hard to locate or disambiguate multiple runs).

### 3) **GET /api/index has side effects**
`GET /api/index` currently **creates** `definitions/test_index.json`.  
GET should be read‑only. This is likely fine for you but breaks REST semantics and can surprise users.

### 4) **Process management**
- No “stop run” or “kill wrapper” endpoint.
- `RUN_PROCESSES` and `WRAPPER_PROCESSES` are in‑memory only (lost on server restart).
**Impact:** Medium.

### 5) **Venv ambiguity**
`server.py` uses `sys.executable` and runs the benchmark from the **environment that started the server**.  
If you start the server with the **root venv**, that’s probably fine. If you start it in the **benchmark venv**, it may not have the MAS dependencies needed for the wrapper.  
**Impact:** Medium (depends on how you run it).

### 6) **CORS is wide‑open**
`allow_origins=["*"]`  
Acceptable for local dev, not for shared LAN.

---

## Readiness Recommendation
**Go‑live for local use: yes**, with the assumption that:
- You will not run multiple runs with the same run_name/agent at the same time.
- You accept that GET index will write files.
- You’re running the server from the root venv.

---

## Next Steps I Recommend
If you want this to be stable for regular use:

1. **Make run directories unique**
   - Use `run_id` as the directory name (or include run_id suffix).
2. **Separate “index compute” from “index read”**
   - Change GET to read only; POST to compute.
3. **Add a stop endpoint**
   - `/api/runs/{id}/stop`
4. **Make venv explicit**
   - Add `benchmarks/goodai-ltm-benchmark/.venv` guidance in WebUI README.
5. **Add minimal frontend build check**
   - Ensure `npm run build` works once before sharing.

---

## If You Want Me to Harden It Now
I can implement the fixes above. Say the word and I’ll proceed.

---

## Optional: Quick Smoke‑Run Checklist
If you want to validate locally now:
1. Start MAS wrapper(s) from UI.
2. Start run with `mas_subset_32k`.
3. Watch:
   - `turn_metrics.jsonl` grows
   - `runstats.json` updates
   - `run_console.log` shows progress
