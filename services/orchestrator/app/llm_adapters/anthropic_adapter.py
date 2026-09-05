"""Anthropic Claude adapter (spec §5.3)."""
from __future__ import annotations

from typing import Any

from .base import LLMAdapter


class ClaudeAdapter(LLMAdapter):
    def __init__(self, api_key: str | None = None) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: str, tools: list[dict], **kwargs: Any) -> Any:
        return self._client.messages.create(
            model=kwargs.get("model", "claude-sonnet-5"),
            max_tokens=kwargs.get("max_tokens", 4096),
            system="You are a research assistant with access to mathematical tools.",
            messages=[{"role": "user", "content": prompt}],
            tools=[self.convert_tool_schema(t) for t in tools],
        )

    def parse_response(self, raw: Any) -> dict[str, Any]:
        text = ""
        tool_calls: list[dict[str, Any]] = []
        for block in raw.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append({"name": block.name, "arguments": dict(block.input)})
        return {"text": text or None, "tool_calls": tool_calls, "finish_reason": raw.stop_reason}

    def convert_tool_schema(self, neutral_tool: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": neutral_tool["name"],
            "description": neutral_tool["description"],
            "input_schema": neutral_tool["parameters"],
        }