# GoodAI Benchmark WebUI

## Backend (API + static UI)
```bash
cd /home/max/code/mas-memory-layer/benchmarks/goodai-ltm-benchmark
PYTHONPATH="$(pwd)" /home/max/code/mas-memory-layer/benchmarks/goodai-ltm-benchmark/.venv/bin/python webui/server.py
```

The backend serves the compiled frontend from `webui/frontend/dist` and exposes
`/api/*` endpoints on `http://localhost:8005`.

## Frontend (build)
```bash
cd /home/max/code/mas-memory-layer/benchmarks/goodai-ltm-benchmark/webui/frontend
npm install
npm run build
```

Rebuild after frontend changes, then restart the backend.

## Wrappers (MAS agents)
Wrappers run in the root `.venv` and are required for `mas-full`, `mas-rag`,
and `mas-full-context` agents.

```bash
cd /home/max/code/mas-memory-layer
./scripts/start_benchmark_wrappers.sh
```

If needed, override the wrapper interpreter used by the WebUI backend:
```bash
export MAS_WRAPPER_PYTHON="/home/max/code/mas-memory-layer/.venv/bin/python"
```

## Notes
- The WebUI defaults to non-interactive runs and passes `-y` to the runner.
- The “Reuse Existing Definitions” toggle controls whether test definitions
	are re-generated or reused.
- Run output is captured in `run_console.log` for every run.
