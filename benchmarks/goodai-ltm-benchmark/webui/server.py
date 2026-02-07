from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from utils.constants import MAIN_DIR, TESTS_DIR
from utils.files import make_run_path
from utils.indexing import build_test_index

BASE_DIR = Path(__file__).resolve().parent
PRESETS_PATH = BASE_DIR.joinpath("presets.json")
WEBUI_LOG_DIR = BASE_DIR.joinpath("logs")
RUN_META_NAME = "run_meta.json"

app = FastAPI(title="GoodAI Benchmark WebUI", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUN_PROCESSES: dict[str, subprocess.Popen] = {}
WRAPPER_PROCESSES: dict[int, subprocess.Popen] = {}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return cast(dict[str, Any], json.load(handle))


def _tail_file(path: Path, max_lines: int = 200) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        lines = handle.readlines()
    return [line.rstrip("\n") for line in lines[-max_lines:]]


def _find_run_meta_files() -> list[Path]:
    return list(TESTS_DIR.glob(f"**/results/*/{RUN_META_NAME}"))


def _run_status(meta_path: Path) -> dict[str, Any]:
    meta = _read_json(meta_path)
    run_dir = meta_path.parent
    run_error = run_dir.joinpath("run_error.json")
    status = "running"
    if meta.get("end_time"):
        status = "completed"
    if run_error.exists():
        status = "stalled"
    return {
        "run_id": meta.get("run_id"),
        "run_name": meta.get("run_name"),
        "agent_name": meta.get("agent_name"),
        "start_time": meta.get("start_time"),
        "end_time": meta.get("end_time"),
        "status": status,
        "path": str(run_dir),
    }


@app.get("/api/presets")
def get_presets() -> dict[str, Any]:
    return _read_json(PRESETS_PATH)


@app.get("/api/runs")
def get_runs() -> dict[str, Any]:
    metas = [_run_status(path) for path in _find_run_meta_files()]
    metas.sort(key=lambda item: item.get("start_time") or "", reverse=True)
    return {"runs": metas}


@app.get("/api/runs/{run_id}/progress")
def get_progress(run_id: str) -> dict[str, Any]:
    meta_path = _locate_run_meta(run_id)
    if meta_path is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run_dir = meta_path.parent
    turn_metrics_path = run_dir.joinpath("turn_metrics.jsonl")
    runstats_path = run_dir.joinpath("runstats.json")

    latest = None
    metrics: list[dict[str, Any]] = []
    if turn_metrics_path.exists():
        with turn_metrics_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                metrics.append(payload)
                latest = payload

    runstats = _read_json(runstats_path)
    return {
        "latest": latest,
        "count": len(metrics),
        "runstats": runstats,
    }


@app.get("/api/runs/{run_id}/logs")
def get_logs(run_id: str) -> dict[str, Any]:
    meta_path = _locate_run_meta(run_id)
    if meta_path is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run_dir = meta_path.parent
    files = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_dir():
            continue
        files.append(
            {
                "name": str(path.relative_to(run_dir)),
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            }
        )
    return {"files": files}


@app.get("/api/runs/{run_id}/logs/{filename:path}")
def get_log_tail(run_id: str, filename: str) -> dict[str, Any]:
    meta_path = _locate_run_meta(run_id)
    if meta_path is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run_dir = meta_path.parent
    target = run_dir.joinpath(filename)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Log not found")
    return {"lines": _tail_file(target)}


@app.post("/api/runs")
def start_run(payload: dict[str, Any]) -> dict[str, Any]:
    config_path = payload.get("config_path")
    agent_name = payload.get("agent_name")
    run_name = payload.get("run_name")
    run_id = payload.get("run_id")
    max_prompt_size = payload.get("max_prompt_size")
    stuck_timeout = payload.get("stuck_timeout", 15)
    metrics_sample_rate = payload.get("metrics_sample_rate", 1.0)
    test_filter = payload.get("test_filter")
    if not config_path or not agent_name:
        raise HTTPException(status_code=400, detail="config_path and agent_name are required")

    run_dir = make_run_path(run_name or "Run", agent_name)
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir.joinpath("run_console.log")

    cmd = [
        sys.executable,
        "runner/run_benchmark.py",
        "--configuration",
        config_path,
        "--agent-name",
        agent_name,
        "--progress",
        "none",
        "--stuck-timeout",
        str(stuck_timeout),
        "--metrics-sample-rate",
        str(metrics_sample_rate),
    ]
    if run_name:
        cmd += ["--run-name", run_name]
    if run_id:
        cmd += ["--run-id", run_id]
    if max_prompt_size:
        cmd += ["--max-prompt-size", str(max_prompt_size)]
    if test_filter:
        cmd += ["--test-filter", test_filter]

    with log_path.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            cmd,
            cwd=str(MAIN_DIR),
            stdout=handle,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )

    RUN_PROCESSES[run_id or run_name or agent_name] = process
    return {"status": "started", "pid": process.pid, "log_path": str(log_path)}


@app.get("/api/index")
def get_index(config_path: str) -> dict[str, Any]:
    output = build_test_index(config_path)
    return _read_json(output)


@app.post("/api/index")
def create_index(payload: dict[str, Any]) -> dict[str, Any]:
    config_path = payload.get("config_path")
    if not config_path:
        raise HTTPException(status_code=400, detail="config_path is required")
    output = build_test_index(config_path)
    return _read_json(output)


@app.post("/api/wrappers/start")
def start_wrapper(payload: dict[str, Any]) -> dict[str, Any]:
    agent_type = payload.get("agent_type")
    port = payload.get("port")
    model = payload.get("model")
    if not agent_type or not port:
        raise HTTPException(status_code=400, detail="agent_type and port are required")
    log_dir = WEBUI_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir.joinpath(f"wrapper-{port}.log")
    cmd = [
        sys.executable,
        "-m",
        "src.evaluation.agent_wrapper",
        "--agent-type",
        agent_type,
        "--port",
        str(port),
    ]
    if model:
        cmd += ["--model", model]

    with log_path.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            cmd,
            cwd=str(Path(__file__).resolve().parents[3]),
            stdout=handle,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )

    WRAPPER_PROCESSES[int(port)] = process
    return {"status": "started", "pid": process.pid, "log_path": str(log_path)}


def _locate_run_meta(run_id: str) -> Path | None:
    for meta in _find_run_meta_files():
        data = _read_json(meta)
        if data.get("run_id") == run_id:
            return meta
    return None


dist_dir = BASE_DIR.joinpath("frontend/dist")
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
else:

    @app.get("/")
    def root() -> JSONResponse:
        return JSONResponse(
            {
                "message": "Build the frontend in webui/frontend to serve the UI.",
                "dist_path": str(dist_dir),
            }
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
