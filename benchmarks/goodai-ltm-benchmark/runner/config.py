from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class RunConfig:
    run_name: str = field(default_factory=lambda: f"Run {uuid4()}({datetime.now()})")
    debug: bool = False
    incompatibilities: list[set[type]] = field(default_factory=list)
    isolated: bool = False
