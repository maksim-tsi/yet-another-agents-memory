import json
import os
import time
from dataclasses import dataclass, field

from openai import ChatCompletion, OpenAI
from transformers import AutoTokenizer, PreTrainedTokenizerFast
from utils.llm import LLMContext, make_assistant_message, make_user_message

from model_interfaces.interface import ChatSession


@dataclass
class HFChatSession(ChatSession):
    is_local: bool = True  # Costs are billed hourly. Hard to track.
    max_prompt_size: int | None = None
    model: str | None = None
    base_url: str | None = None
    context: LLMContext = field(default_factory=lambda: [])
    max_response_tokens: int = 2048
    client: OpenAI | None = None
    tokenizer: PreTrainedTokenizerFast | None = None
    tokens_used_last: int = 0

    @property
    def name(self):
        name = f"{super().name} - {self.model} - {self.max_prompt_size}"
        return name.replace("/", "-")

    def __post_init__(self):
        super().__post_init__()
        if self.base_url is None:
            self.base_url = os.getenv("HUGGINGFACE_API_BASE")
        assert self.base_url is not None
        assert self.model is not None
        self.client = OpenAI(
            base_url=f"{self.base_url}/v1/",
            api_key=os.getenv("HUGGINGFACE_API_KEY"),
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model.removeprefix("huggingface/"))

    def try_twice(self) -> ChatCompletion:
        assert self.client is not None
        for i in range(2):
            try:
                return self.client.chat.completions.create(
                    model="tgi",
                    messages=self.context,
                    max_tokens=self.max_response_tokens,
                    temperature=0,
                )
            except Exception as exc:
                if i > 0:
                    raise exc
                time.sleep(3)

    def reply(self, user_message: str, agent_response: str | None = None) -> str:
        self.context.append(make_user_message(user_message))
        assert self.max_prompt_size is not None
        self.tokens_used_last += self.token_len(user_message) + self.max_response_tokens
        while self.tokens_used_last > self.max_prompt_size:
            self.tokens_used_last -= self.token_len(self.context[0]["content"])
            self.tokens_used_last -= self.token_len(self.context[1]["content"])
            self.context = self.context[2:]
        if agent_response is None:
            completion = self.try_twice()
            self.tokens_used_last = completion.usage.total_tokens
            message_content = completion.choices[0].message.content or ""
            response = message_content.removesuffix("</s>")
        else:
            self.tokens_used_last -= self.max_response_tokens - self.token_len(agent_response)
            response = agent_response
        self.context.append(make_assistant_message(response))
        return response

    def reset(self):
        self.context = []

    def save(self):
        fname = self.save_path.joinpath("context.json")
        with open(fname, "w") as fd:
            json.dump(self.context, fd)

    def load(self):
        fname = self.save_path.joinpath("context.json")
        with open(fname) as fd:
            self.context = json.load(fd)

    def token_len(self, text: str) -> int:
        assert self.tokenizer is not None
        return len(self.tokenizer.tokenize(text=text))
