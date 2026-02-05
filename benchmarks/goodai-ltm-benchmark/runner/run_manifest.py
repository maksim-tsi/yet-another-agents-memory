from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class RunManifest:
    run_id: str
    run_name: str
    agent_name: str
    config_path: str
    progress: str
    stuck_timeout_minutes: int
    turn_metrics: bool
    metrics_sample_rate: float
    start_time: str
    end_time: str | None = None

    @classmethod
    def start(
        cls,
        *,
        run_id: str,
        run_name: str,
        agent_name: str,
        config_path: str,
        progress: str,
        stuck_timeout_minutes: int,
        turn_metrics: bool,
        metrics_sample_rate: float,
    ) -> RunManifest:
        return cls(
            run_id=run_id,
            run_name=run_name,
            agent_name=agent_name,
            config_path=config_path,
            progress=progress,
            stuck_timeout_minutes=stuck_timeout_minutes,
            turn_metrics=turn_metrics,
            metrics_sample_rate=metrics_sample_rate,
            start_time=datetime.now(UTC).isoformat(),
        )

    def finish(self) -> None:
        self.end_time = datetime.now(UTC).isoformat()

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(self), handle, indent=2)
