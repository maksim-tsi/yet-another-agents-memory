from dataclasses import dataclass, field
from pathlib import Path

from dataset_interfaces.gpt_generated import GPTGenerated
from dataset_interfaces.interface import TestExample
from utils.constants import DATA_DIR


@dataclass
class DelayedRecallDataset(GPTGenerated):
    name: str = "Delayed Recall"
    description: str = "Give the agent a number of facts about a a fictional world, and then ask 10 questions about these facts."
    generation_file: Path = field(
        default_factory=lambda: DATA_DIR.joinpath("gpt_generation_prompts/1-1_delayed_recall.json")
    )
    reset_message: str = (
        "Forget all of the facts given to you about the fictional world before this message."
    )

    def generate_examples(self, num_examples: int) -> list[TestExample]:
        example_list = super().generate_examples(num_examples)
        for example in example_list:
            example.script[0] = (
                f"Take a look at the following facts about a fictional world:\n\n{example.script[0]}"
            )
            for i, (line, is_question) in enumerate(
                zip(example.script, example.is_question, strict=False)
            ):
                if not is_question:
                    continue
                intro = self.random.choice(
                    [
                        "One question about the fictional world.",
                        "Answer this question about the fictional world:",
                        "Going back to the fictional world,",
                        "Look, about the fictional world...",
                    ]
                )
                example.script[i] = f"{intro} {line}"
                # The number of script lines has changed, redo the waits.
                example.waits = []
                example.default_waits()
        return example_list
