from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class StuckWatchdog:
    timeout: timedelta
    run_error_path: Path
    last_event: datetime | None = None

    def touch(self) -> None:
        self.last_event = datetime.now(UTC)

    def check_or_raise(self, context: dict[str, Any]) -> None:
        if self.timeout.total_seconds() <= 0:
            return
        now = datetime.now(UTC)
        last = self.last_event or now
        if (now - last) < self.timeout:
            return
        payload = {
            "timestamp": now.isoformat(),
            "last_event": last.isoformat(),
            "timeout_seconds": int(self.timeout.total_seconds()),
            "context": context,
        }
        self.run_error_path.parent.mkdir(parents=True, exist_ok=True)
        with self.run_error_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        raise RuntimeError("Benchmark stalled: no activity within the configured timeout window.")
