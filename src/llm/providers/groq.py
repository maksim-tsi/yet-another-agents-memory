"""Groq provider implementation using Groq Python SDK."""

from __future__ import annotations

import asyncio
import logging

from src.llm.providers.base import BaseProvider, LLMResponse, ProviderHealth

logger = logging.getLogger(__name__)


class GroqProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(name="groq")
        from groq import Groq

        self.client = Groq(api_key=api_key)

    async def generate(self, prompt: str, model: str | None = None, **kwargs) -> LLMResponse:
        model = model or "openai/gpt-oss-120b"

        def sync_call():
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.0),
                max_tokens=kwargs.get("max_output_tokens", 256),
            )
            return response

        response = await asyncio.to_thread(sync_call)

        usage = getattr(response, "usage", None)
        usage_dict = None
        if usage:
            usage_dict = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "response_tokens": getattr(usage, "completion_tokens", None),
                "total": getattr(usage, "total_tokens", None),
            }

        text = ""
        try:
            text = response.choices[0].message.content
        except Exception:
            text = getattr(response, "text", "")

        return LLMResponse(text=text, provider=self.name, model=model, usage=usage_dict)

    async def health_check(self) -> ProviderHealth:
        try:

            def sync_call():
                # Minimal call to validate client
                return self.client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "user", "content": "Ping"}],
                    temperature=0.0,
                    max_tokens=1,
                )

            await asyncio.to_thread(sync_call)
            return ProviderHealth(name=self.name, healthy=True, details="OK")
        except Exception as exc:
            logger.warning("Groq health check failed: %s", exc)
            return ProviderHealth(name=self.name, healthy=False, last_error=str(exc))
