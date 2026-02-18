from typing import Any

from colorama import Fore, Style


def render_context(context: list[dict[str, Any]]) -> None:
    for ctx in context:
        if ctx["role"] == "user":
            print(Fore.YELLOW + f"USER:\n{ctx['content']}\n")
        if ctx["role"] == "assistant":
            print(Fore.CYAN + f"ASSISTANT:\n{ctx['content']}\n")

    print(Style.RESET_ALL)


def flatten_context(context: list[dict[str, Any]]) -> str:
    string = ""
    for ctx in context:
        string += ctx["content"]

    return string


def search_context(
    context: list[dict[str, Any]], content: str | None = None, timestamp: str | None = None
) -> int:
    for idx, c in enumerate(context):
        if content and c["content"] != content:
            continue

        if timestamp and c["timestamp"].__str__() != timestamp:
            continue

        return idx

    raise ValueError(
        "Context search failed!\n"
        f"content = {content!r}\n"
        f"timestamp = {timestamp}\n"
        f"history:\n{context}"
    )
