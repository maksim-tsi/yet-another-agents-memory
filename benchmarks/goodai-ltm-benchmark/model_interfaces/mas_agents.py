import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, cast

import requests
from utils.llm import count_tokens_for_model

from model_interfaces.interface import ChatSession


@dataclass
class MASWrapperSession(ChatSession):
    """Base GoodAI chat session that proxies requests to the MAS wrapper service."""

    endpoint: str = "http://localhost:8080"
    session_prefix: str = "full"
    max_prompt_size: int | None = None
    request_timeout: float = 90.0
    max_retries: int = 3
    backoff_seconds: float = 0.5
    model_for_cost: str = "gemini-2.5-flash-lite"
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    turn_id: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.max_prompt_size is not None:
            self.max_message_size = self.max_prompt_size

        env_timeout = os.environ.get("MAS_WRAPPER_TIMEOUT")
        if env_timeout:
            self.request_timeout = float(env_timeout)

    @property
    def name(self) -> str:
        return f"{super().name} - {self.session_prefix}"

    def _prefixed_session_id(self) -> str:
        prefix = f"{self.session_prefix}:"
        if self.session_id.startswith(prefix):
            return self.session_id
        return f"{self.session_prefix}:{self.session_id}"

    def reply(self, user_message: str, agent_response: str | None = None) -> str:
        if agent_response is not None:
            return agent_response

        payload = {
            "session_id": self._prefixed_session_id(),
            "role": "user",
            "content": user_message,
            "turn_id": self.turn_id,
            "metadata": {"run_name": self.run_name},
        }

        response_json = self._post_with_retry(payload)
        self.turn_id += 1

        self.last_metadata = response_json.get("metadata")
        response_text = cast(str, response_json.get("content", ""))
        self._update_costs(user_message, response_text)
        return response_text

    def _post_with_retry(self, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        backoff = self.backoff_seconds
        url = f"{self.endpoint}/run_turn"

        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json=payload, timeout=self.request_timeout)
                if response.status_code >= 500:
                    raise RuntimeError(f"Server error {response.status_code}: {response.text}")
                if response.status_code >= 400:
                    raise RuntimeError(f"Request failed {response.status_code}: {response.text}")
                return cast(dict[str, Any], response.json())
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries - 1:
                    break
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError(f"Failed to call MAS wrapper: {last_error}")

    def _update_costs(self, prompt: str, response: str) -> None:
        if self.is_local:
            return

        try:
            prompt_tokens = count_tokens_for_model(text=prompt)
            response_tokens = count_tokens_for_model(text=response)
        except Exception:
            prompt_tokens = len(prompt.split())
            response_tokens = len(response.split())

        cost_in = float(os.environ.get("MAS_WRAPPER_COST_IN", "0.000001"))
        cost_out = float(os.environ.get("MAS_WRAPPER_COST_OUT", "0.000001"))
        estimated = (prompt_tokens * cost_in) + (response_tokens * cost_out)
        self.costs_usd += max(estimated, 1e-9)

    def reset(self) -> None:
        self.session_id = uuid.uuid4().hex
        self.turn_id = 0

    def save(self) -> None:
        fname = self.save_path.joinpath("session.json")
        payload = {
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "endpoint": self.endpoint,
            "session_prefix": self.session_prefix,
        }
        with open(fname, "w") as fd:
            json.dump(payload, fd)

    def load(self) -> None:
        fname = self.save_path.joinpath("session.json")
        if not fname.exists():
            return
        with open(fname) as fd:
            payload = json.load(fd)
        self.session_id = payload.get("session_id", self.session_id)
        self.turn_id = payload.get("turn_id", self.turn_id)
        self.endpoint = payload.get("endpoint", self.endpoint)
        self.session_prefix = payload.get("session_prefix", self.session_prefix)


@dataclass
class MASFullSession(MASWrapperSession):
    endpoint: str = "http://localhost:8080"
    session_prefix: str = "full"


@dataclass
class MASRAGSession(MASWrapperSession):
    endpoint: str = "http://localhost:8081"
    session_prefix: str = "rag"


@dataclass
class MASFullContextSession(MASWrapperSession):
    endpoint: str = "http://localhost:8082"
    session_prefix: str = "full_context"
