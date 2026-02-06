import json
from dataclasses import dataclass, field
from pathlib import Path

from dataset_interfaces.factory import DATASETS_BY_NAME
from utils.files import make_result_path, parse_result_path


@dataclass
class TestResult:
    run_name: str
    agent_name: str
    dataset_name: str
    example_id: str
    description: str = ""
    task_log: list[str] = field(default_factory=list)
    expected_responses: list[str] = field(default_factory=list)
    actual_responses: list[str] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    score: float = 0.0
    max_score: float = 0.0
    tokens: int | None = None
    characters: int | None = None
    repetition: int = 0
    full_log: list[str] = field(default_factory=list)
    needles: int = 0

    def __post_init__(self) -> None:
        self._saved_attrs = [
            "task_log",
            "actual_responses",
            "score",
            "max_score",
            "reasoning",
            "tokens",
            "characters",
            "full_log",
            "expected_responses",
            "needles",
        ]

    def __str__(self) -> str:
        string = ""
        string += f"Dataset Name: {self.dataset_name}\n"
        string += f"Run Name: {self.run_name}\n"
        string += f"Description: {self.description}\nTask log:\n"
        for idx, s in enumerate(self.task_log):
            string += f"\t{s}\n"
            if (idx + 1) % 2 == 0:
                string += "\n"
        string += f"\nExpected response: {self.expected_responses}\n"
        string += f"\nActual response: {' '.join(self.actual_responses)}\n"
        string += f"\nReasoning: {self.reasoning}\n"
        string += f"\nScore: {self.score}/{self.max_score}\n"
        string += f"Tokens: {self.tokens}\n"
        string += f"Characters: {self.characters}\n"
        return string

    @property
    def unique_id(self) -> str:
        return f"{self.dataset_name} - {self.example_id}"

    @property
    def path(self) -> Path:
        return make_result_path(
            self.run_name, self.agent_name, self.dataset_name, self.example_id, self.repetition
        )

    def save(self) -> None:
        file_path = self.path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as fd:
            json.dump({k: getattr(self, k) for k in self._saved_attrs}, fd, indent=2)

    def load(self) -> None:
        with open(self.path) as fd:
            d = json.load(fd)
        for k in self._saved_attrs:
            setattr(self, k, d[k])

    @classmethod
    def from_file(cls, path: Path | str) -> "TestResult":
        parts = parse_result_path(path)
        result = TestResult(
            run_name=str(parts["run_name"]),
            agent_name=str(parts["agent_name"]),
            dataset_name=str(parts["dataset_name"]),
            example_id=str(parts["example_id"]),
            repetition=int(parts["repetition"]),
        )
        result.description = DATASETS_BY_NAME[result.dataset_name].description
        result.load()
        return result
