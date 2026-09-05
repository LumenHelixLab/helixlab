"""Google Gemini adapter (spec §5.3) — STUB.

The spec marks Gemini parsing as SDK-version-dependent. Implement against the
installed google-generativeai version in sprint 1:
- generate: genai.GenerativeModel(model_name, tools=[{"function_declarations":
  [...]}]).generate_content(prompt)
- convert_tool_schema: {name, description, parameters} (flat)
- parse_response: extract function_call parts from the candidate content.

Do NOT ship this stub to production paths — LLMAdapterFactory raises until the
three methods are implemented.
"""
from __future__ import annotations

from typing import Any

from .base import LLMAdapter


class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key: str | None = None) -> None:
        raise NotImplementedError(
            "GeminiAdapter is a stub (spec §5.3). Pin google-generativeai and "
            "implement generate/parse_response/convert_tool_schema first."
        )

    def generate(self, prompt: str, tools: list[dict], **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    def parse_response(self, raw: Any) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def convert_tool_schema(self, neutral_tool: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError