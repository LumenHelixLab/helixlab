"""OpenAI adapter (spec §5.3). Also the template for OpenAI-compatible
providers (Kimi, Llama-via-Together) via `base_url` overrides."""
from __future__ import annotations

from typing import Any

from .base import LLMAdapter


class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        import openai

        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, tools: list[dict], **kwargs: Any) -> Any:
        return self._client.chat.completions.create(
            model=kwargs.get("model", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            tools=[self.convert_tool_schema(t) for t in tools],
            tool_choice="auto",
        )

    def parse_response(self, raw: Any) -> dict[str, Any]:
        # Support both SDK objects and plain dicts.
        choice = raw["choices"][0] if isinstance(raw, dict) else raw.choices[0]
        message = choice["message"] if isinstance(choice, dict) else choice.message
        raw_calls = message.get("tool_calls", []) if isinstance(message, dict) else (message.tool_calls or [])
        tool_calls = [
            {
                "name": tc["function"]["name"] if isinstance(tc, dict) else tc.function.name,
                "arguments": self._decode(tc),
            }
            for tc in raw_calls
        ]
        text = message.get("content") if isinstance(message, dict) else message.content
        finish = choice["finish_reason"] if isinstance(choice, dict) else choice.finish_reason
        return {"text": text, "tool_calls": tool_calls, "finish_reason": finish}

    def convert_tool_schema(self, neutral_tool: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": neutral_tool["name"],
                "description": neutral_tool["description"],
                "parameters": neutral_tool["parameters"],
            },
        }

    @staticmethod
    def _decode(tc: Any) -> dict[str, Any]:
        fn = tc["function"] if isinstance(tc, dict) else tc.function
        args = fn["arguments"] if isinstance(fn, dict) else fn.arguments
        import json

        return json.loads(args or "{}")