from collections.abc import Iterator
from dataclasses import dataclass
from json import JSONDecodeError

import pystache
from dataset_interfaces.interface import DatasetInterface, TestExample
from goodai.helpers.json_helper import sanitize_and_parse_json
from utils.llm import GPT_CHEAPEST, make_user_message
from utils.text import rouge_l, standardise
from utils.ui import colour_print

REQUESTS = [
    "ask you for the time",
    "ask you to read my mail for me",
    "sneeze with 'Achooo!'",
    "write 'hppy' instead of 'happy'",
    "express a desire to eat sugary treats",
    "say that I am feeling ill",
    "say that I am tired or sleepy",
]

RESPONSE = [
    "It's Party time!",
    "Your letter opener is in your office",
    "Here is a tissue for you",
    "You misspelled 'happy' as 'hppy'",
    "resist temptation and stick to your diet",
    "I am sorry to hear that. I hope you recover soon",
    "Either go to bed then or drink something containing caffeine",
]


TRIGGERS = [
    "What is the current time?",
    "Please read my mail for me.",
    "Achoo!",
    "I am hppy today!",
    "I am pretty snacky for some sweet treats.",
    "I don't feel very well.",
    "I am pretty tired.",
]

eval_prompt = """
Take a look at the following text:
"{message}"

Determine whether the sentence "{sentence}" is present or not in the text. If the sentence is present, extract the piece of text that features the targeted sentence. Answer in JSON form, like this:
{{"present": true or false, "sentence": "targeted sentence"}}
""".strip()


@dataclass
class TriggerResponseDataset(DatasetInterface):
    name: str = "Trigger Response"
    description: str = (
        "Tell the agent to respond in a particular way when a trigger is given. Test the agent."
    )
    trigger_activations: int = 3
    reset_message: str = "Cancel any instructions as to what sentence you should say whenever I do something in particular."
    rouge_score_threshold: float = 0.75

    def request_num_generator(self) -> Iterator[int]:
        indices = list(range(len(REQUESTS)))
        warned = False
        while True:
            self.random.shuffle(indices)
            yield from indices
            if warned:
                continue
            warned = True
            colour_print(
                "red",
                "WARNING: The number of TriggerResponse setups has been exceeded. There will inevitably "
                "be some repetitions.",
            )

    def generate_examples(self, num_examples):
        examples = []
        setup = "Whenever I {{request}} then say: '{{response}}'"

        for _, request_num in zip(range(num_examples), self.request_num_generator(), strict=False):
            answer_list = []
            request = REQUESTS[request_num]
            response = RESPONSE[request_num]
            trigger = TRIGGERS[request_num]

            script = [pystache.render(setup, {"request": request, "response": response})]
            is_question = [False]

            for _ in range(self.trigger_activations):
                script.append(trigger)
                is_question.append(True)
                answer_list.append(response)

            example = TestExample(
                dataset_generator=self,
                script=script,
                expected_responses=answer_list,
                is_question=is_question,
            )
            examples.append(example)

        return examples

    def evaluate_single(self, actual: str, expected: str) -> tuple[int, str]:
        actual_std = standardise(actual)
        expected_std = standardise(expected)
        if (
            expected_std in actual_std
            or rouge_l(expected_std, actual_std) > self.rouge_score_threshold
        ):
            return 1, f"'{expected}' is in the response."
        context = [make_user_message(eval_prompt.format(message=actual, sentence=expected))]
        eval_str = self.ask_llm(context, GPT_CHEAPEST)
        try:
            eval_json = sanitize_and_parse_json(eval_str)
            present = eval_json["present"]
            if present:
                present = (
                    rouge_l(expected_std, standardise(eval_json["sentence"]))
                    > self.rouge_score_threshold
                )
        except (ValueError, JSONDecodeError, KeyError) as exc:
            return 0, f"Could not evaluate due to a JSON parsing error: {exc!r}"
        not_str = "" if present else "not "
        return int(present), f"'{expected}' is {not_str}in the response."

    def evaluate_correct(
        self, questions: list[str], responses: list[str], expected_answers: list[str]
    ) -> tuple[int, int, list[str]]:
        score = 0
        max_score = len(expected_answers)
        reasoning = list()
        for r, e in zip(responses, expected_answers, strict=False):
            score_single, reasoning_single = self.evaluate_single(r, e)
            score += score_single
            reasoning.append(reasoning_single)
        return score, max_score, reasoning
