from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pystache
from goodai.helpers.json_helper import sanitize_and_parse_json
from utils.llm import GPT_CHEAPEST, ask_llm

from dataset_interfaces.interface import CallBackTestExample, DatasetInterface, TestExample

PROMPT = """Generate data and questions based on the structure and instructions below.
- For content: {{content}} 
- For question: {{question}}
- For answer: {{answer}}

Structure your response as such:
{
    "content": [""],
    "question": [""],
    "answer": [""]
}"""


@dataclass
class GPTGenerated(DatasetInterface, ABC):
    generation_file: str | Path | None = None
    temperature: float = 1.0
    generation_model: str = GPT_CHEAPEST
    max_attempts: int = 10

    def __post_init__(self) -> None:
        if self.generation_file is None:
            raise ValueError("GPTGenerated datasets require a file path to read from.")

    def generate_examples(self, num_examples: int) -> list[TestExample]:
        examples = []
        generation_file = self.generation_file
        if generation_file is None:
            raise ValueError("GPTGenerated datasets require a file path to read from.")
        prompt_data = self.load_json(generation_file)

        for _ in range(num_examples):
            script = []
            is_question = []
            expected_responses = []
            # Generate a set of examples using GPT
            generation_prompt = pystache.render(PROMPT, prompt_data)
            context = [
                {"role": "system", "content": "You are a helpful creative agent"},
                {"role": "user", "content": generation_prompt},
            ]
            correct = False
            for _ in range(self.max_attempts):
                try:
                    result = ask_llm(
                        context, temperature=self.temperature, model=self.generation_model
                    )
                    generated = sanitize_and_parse_json(result)
                    correct = True
                    break
                except Exception:
                    pass
            if not correct:
                raise ValueError(
                    f"GPT powered generation failed after {self.max_attempts} attempts! You can choose to rerun the generation."
                )

            script.append("\n".join(generated["content"]))
            is_question.append(False)

            for q, a in zip(generated["question"], generated["answer"], strict=False):
                is_question.append(True)
                script.append(q)
                expected_responses.append(a)

            example_class: type[TestExample] = (
                CallBackTestExample if self.uses_callback else TestExample
            )

            example = example_class(
                dataset_generator=self,
                script=script,
                expected_responses=expected_responses,
                is_question=is_question,
                uses_callback=self.uses_callback,
            )

            examples.append(example)

        return examples

    def evaluate_correct(
        self, questions: list[str], responses: list[str], expected_answers: list[Any]
    ) -> tuple[float, float, list[str]]:
        return self.evaluate_correct_gpt(questions, responses, expected_answers)
