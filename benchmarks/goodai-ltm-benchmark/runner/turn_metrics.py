from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class TurnMetrics:
    timestamp: str
    run_id: str
    session_id: str
    turn_id: int
    test_id: str
    dataset_name: str
    llm_ms: float | None
    storage_ms: float | None
    total_ms: float | None
    tokens_in: int
    tokens_out: int
    status: str
    error: str | None = None

    @classmethod
    def now(
        cls,
        *,
        run_id: str,
        session_id: str,
        turn_id: int,
        test_id: str,
        dataset_name: str,
        llm_ms: float | None,
        storage_ms: float | None,
        total_ms: float | None,
        tokens_in: int,
        tokens_out: int,
        status: str,
        error: str | None = None,
    ) -> TurnMetrics:
        return cls(
            timestamp=datetime.now(UTC).isoformat(),
            run_id=run_id,
            session_id=session_id,
            turn_id=turn_id,
            test_id=test_id,
            dataset_name=dataset_name,
            llm_ms=llm_ms,
            storage_ms=storage_ms,
            total_ms=total_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            status=status,
            error=error,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TurnMetricsWriter:
    def __init__(self, path: Path, sample_rate: float = 1.0):
        if sample_rate <= 0 or sample_rate > 1:
            raise ValueError("sample_rate must be within (0, 1].")
        self.path = path
        self.sample_rate = sample_rate
        self._rng = random.Random(0)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _should_sample(self) -> bool:
        if self.sample_rate >= 1.0:
            return True
        return self._rng.random() <= self.sample_rate

    def write(self, metrics: TurnMetrics) -> None:
        if not self._should_sample():
            return
        payload = json.dumps(metrics.to_dict(), ensure_ascii=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
