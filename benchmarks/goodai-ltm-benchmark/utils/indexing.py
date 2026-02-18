from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from dataset_interfaces.factory import DatasetFactory
from dataset_interfaces.interface import TestExample

from utils.constants import MAIN_DIR
from utils.files import make_run_path


def build_test_index(config_path: str, output_path: str | None = None) -> Path:
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = MAIN_DIR.joinpath(config_file)
    with config_file.open("rb") as handle:
        loaded_yaml = yaml.safe_load(handle)

    run_name = loaded_yaml["config"]["run_name"]
    datasets_yaml = loaded_yaml["datasets"]
    examples: list[TestExample] = []
    for ds in datasets_yaml["datasets"]:
        examples.extend(DatasetFactory.create_examples(ds, datasets_yaml["args"], 4096))

    summary: dict[str, Any] = {
        "run_name": run_name,
        "config_path": str(config_file),
        "examples": [],
        "totals": {"examples": len(examples), "questions": 0},
    }
    total_questions = 0
    for example in examples:
        item = {
            "dataset": example.dataset_name,
            "example_id": example.example_id,
            "questions": example.number_of_questions,
            "description": example.description,
        }
        total_questions += example.number_of_questions
        summary["examples"].append(item)
    summary["totals"]["questions"] = total_questions

    if output_path is None:
        output_file = make_run_path(run_name).joinpath("definitions/test_index.json")
    else:
        output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    return output_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a GoodAI benchmark test index.")
    parser.add_argument("--config", required=True, help="Path to benchmark YAML config.")
    parser.add_argument("--output", required=False, help="Output path for JSON index.")
    args = parser.parse_args()
    build_test_index(args.config, args.output)
