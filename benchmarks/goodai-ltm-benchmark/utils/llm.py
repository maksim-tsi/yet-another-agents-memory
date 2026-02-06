import logging
import os
import time
from collections.abc import Callable

from google import genai
from google.genai import types
from transformers import AutoTokenizer

try:  # Optional import for richer error typing
    from google.api_core import exceptions as google_exceptions
except Exception:  # pragma: no cover - defensive fallback
    google_exceptions = None

logger = logging.getLogger(__name__)

LLMMessage = dict[str, str]
LLMContext = list[LLMMessage]

GEMINI_DEFAULT_MODEL = "gemini-2.5-flash-lite"
GEMINI_MAX_CONTEXT_TOKENS = int(os.getenv("MAS_GEMINI_MAX_CONTEXT_TOKENS", "96000"))
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("MAS_GEMINI_MAX_OUTPUT_TOKENS", "8192"))
GEMINI_COST_IN = float(os.getenv("MAS_GEMINI_COST_IN", "0.0"))
GEMINI_COST_OUT = float(os.getenv("MAS_GEMINI_COST_OUT", "0.0"))

GPT_CHEAPEST = GEMINI_DEFAULT_MODEL
GPT_4_TURBO_BEST = GEMINI_DEFAULT_MODEL
LEAST_EFFICIENT_TOKENISER = GEMINI_DEFAULT_MODEL

_CLIENT: genai.Client | None = None


class GeminiContextWindowExceededError(Exception):
    """Raised when the Gemini context window is exceeded before dispatch."""

    def __init__(self, model: str, max_tokens: int, requested_tokens: int) -> None:
        super().__init__(
            f"Gemini context window exceeded: requested {requested_tokens} tokens, max {max_tokens}"
        )
        self.model = model
        self.max_tokens = max_tokens
        self.requested_tokens = requested_tokens


def _get_client() -> genai.Client:
    global _CLIENT
    if _CLIENT is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set")
        _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def _build_gemini_contents(
    context: LLMContext,
) -> tuple[list[types.Content], list[types.Part] | None]:
    system_parts: list[str] = []
    contents: list[types.Content] = []
    for message in context:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            system_parts.append(content)
            continue
        gemini_role = "user" if role == "user" else "model"
        contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=content)],
            )
        )
    system_instruction = None
    if system_parts:
        system_text = "\n\n".join(system_parts)
        system_instruction = [types.Part.from_text(text=system_text)]
    return contents, system_instruction


def _count_tokens_response_total(response: object) -> int | None:
    total = getattr(response, "total_tokens", None)
    if total is None:
        total = getattr(response, "total_token_count", None)
    return total


def count_tokens_gemini(
    model: str, context: LLMContext | None = None, text: str | None = None
) -> int:
    client = _get_client()
    if context is not None:
        contents, system_instruction = _build_gemini_contents(context)
        if system_instruction:
            system_text = system_instruction[0].text
            contents = [
                types.Content(
                    role="user", parts=[types.Part.from_text(text=f"[system]\n{system_text}")]
                ),
                *contents,
            ]
        response = client.models.count_tokens(model=model, contents=contents)
        return int(_count_tokens_response_total(response) or 0)
    if text is None:
        return 0
    response = client.models.count_tokens(model=model, contents=text)
    return int(_count_tokens_response_total(response) or 0)


def get_max_prompt_size(model: str) -> int:
    return GEMINI_MAX_CONTEXT_TOKENS


def token_cost(model: str) -> tuple[float, float]:
    """Return per-token costs for the Gemini model using env-configured rates."""
    _ = model
    return GEMINI_COST_IN, GEMINI_COST_OUT


def ensure_context_len(
    context: LLMContext,
    model: str = LEAST_EFFICIENT_TOKENISER,
    max_len: int | None = None,
    response_len: int = 0,
) -> tuple[LLMContext, int]:
    max_len = max_len or get_max_prompt_size(model)
    messages: list[LLMMessage] = []
    if len(context) > 0 and context[0]["role"] == "system":
        sys_prompt = context[:1]
        context = context[1:]
    else:
        sys_prompt = []

    context_tokens = count_tokens_for_model(model=model, context=sys_prompt + context)

    reversed_context = list(reversed(context))
    if not reversed_context:
        return sys_prompt, context_tokens

    # Latest user's message is always added (there should always be one)
    messages.append(reversed_context.pop(0))

    # Take messages as pairs and reverse them for the check
    for message_pair in zip(reversed_context[::2], reversed_context[1::2], strict=False):
        message_tokens = count_tokens_for_model(model=model, context=list(reversed(message_pair)))
        if context_tokens + message_tokens + response_len > max_len:
            break
        messages.extend(message_pair)
        context_tokens += message_tokens
    messages.reverse()
    context = sys_prompt + messages
    return context, context_tokens


def _is_rate_limit(exc: Exception) -> bool:
    if google_exceptions and isinstance(exc, google_exceptions.ResourceExhausted):
        return True
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)


def _extract_usage_metadata(response: object) -> dict[str, int | None]:
    usage = getattr(response, "usage_metadata", None)
    if not usage:
        return {"prompt_tokens": None, "response_tokens": None, "total": None}
    return {
        "prompt_tokens": getattr(usage, "prompt_token_count", None),
        "response_tokens": getattr(usage, "candidates_token_count", None),
        "total": getattr(usage, "total_token_count", None),
    }


def ask_gemini(
    context: LLMContext,
    model: str,
    temperature: float = 1,
    context_length: int | None = None,
    cost_callback: Callable[[float], None] | None = None,
    timeout: float = 300,
    max_response_tokens: int | None = 1024,
) -> str:
    model = model or GEMINI_DEFAULT_MODEL
    max_response_tokens = (
        GEMINI_MAX_OUTPUT_TOKENS if max_response_tokens is None else max_response_tokens
    )
    max_context = context_length or GEMINI_MAX_CONTEXT_TOKENS
    context, _ = ensure_context_len(context, model, max_context, response_len=max_response_tokens)

    client = _get_client()
    contents, system_instruction = _build_gemini_contents(context)
    prompt_tokens = count_tokens_gemini(model=model, context=context)

    logger.debug(
        "Gemini prompt token estimate: model=%s prompt_tokens=%s max_context=%s",
        model,
        prompt_tokens,
        max_context,
    )

    if prompt_tokens + max_response_tokens > max_context:
        raise GeminiContextWindowExceededError(
            model, max_context, prompt_tokens + max_response_tokens
        )

    config_params: dict[str, object] = {
        "temperature": temperature,
        "max_output_tokens": max_response_tokens,
    }
    if system_instruction:
        config_params["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_params)

    last_exc: Exception | None = None
    backoff = 1.0
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            usage = _extract_usage_metadata(response)
            logger.debug(
                "Gemini usage: model=%s prompt_tokens=%s response_tokens=%s total=%s",
                model,
                usage.get("prompt_tokens"),
                usage.get("response_tokens"),
                usage.get("total"),
            )
            if cost_callback is not None and usage.get("prompt_tokens") is not None:
                cost = (usage["prompt_tokens"] or 0) * GEMINI_COST_IN
                cost += (usage.get("response_tokens") or 0) * GEMINI_COST_OUT
                cost_callback(cost)
            return getattr(response, "text", "")
        except Exception as exc:  # pragma: no cover - network error handling
            last_exc = exc
            if attempt >= 2 or not _is_rate_limit(exc):
                break
            logger.debug("Gemini rate limit encountered, backing off %.1fs", backoff)
            time.sleep(backoff)
            backoff *= 2

    raise last_exc or RuntimeError("Gemini request failed")


def ask_llm(
    context: LLMContext,
    model: str,
    temperature: float = 1,
    context_length: int | None = None,
    cost_callback: Callable[[float], None] | None = None,
    timeout: float = 300,
    max_response_tokens: int | None = 1024,
) -> str:
    return ask_gemini(
        context=context,
        model=model,
        temperature=temperature,
        context_length=context_length,
        cost_callback=cost_callback,
        timeout=timeout,
        max_response_tokens=max_response_tokens,
    )


def make_message(role: str, content: str) -> LLMMessage:
    assert role in {"system", "user", "assistant"}
    return {"role": role, "content": content}


def make_system_message(content: str) -> LLMMessage:
    return make_message("system", content)


def make_user_message(content: str) -> LLMMessage:
    return make_message("user", content)


def make_assistant_message(content: str) -> LLMMessage:
    return make_message("assistant", content)


def count_tokens_for_model(
    model: str = LEAST_EFFICIENT_TOKENISER,
    context: LLMContext | None = None,
    script: list[str] | None = None,
    text: str | None = None,
) -> int:
    token_count = 0

    if model and "huggingface" in model.lower():
        model_only = model[model.index("/") + 1 :]
        tokeniser = AutoTokenizer.from_pretrained(model_only)

        if context:
            c = context[1:] if context[0]["role"] == "system" else context
            token_count += len(tokeniser.apply_chat_template(c))

        if script:
            for line in script:
                token_count += len(tokeniser.encode(line))

        if text:
            token_count += len(tokeniser.encode(text))
        return token_count

    try:
        if context:
            token_count += count_tokens_gemini(model=model or GEMINI_DEFAULT_MODEL, context=context)

        if script:
            for line in script:
                token_count += count_tokens_gemini(model=model or GEMINI_DEFAULT_MODEL, text=line)

        if text:
            token_count += count_tokens_gemini(model=model or GEMINI_DEFAULT_MODEL, text=text)

        return token_count
    except Exception as exc:  # pragma: no cover - fallback for missing API keys
        logger.debug("Token count fallback in use due to error: %s", exc)
        fallback_count = 0
        if context:
            fallback_count += sum(len(m.get("content", "").split()) for m in context)
        if script:
            fallback_count += sum(len(line.split()) for line in script)
        if text:
            fallback_count += len(text.split())
        return fallback_count


def create_huggingface_chat_context(model: str, context: LLMContext) -> str:
    model_only = model[model.index("/") + 1 :]
    tokenizer = AutoTokenizer.from_pretrained(model_only)
    c = context[1:] if context[0]["role"] == "system" else context
    return str(tokenizer.apply_chat_template(c, tokenize=False))
