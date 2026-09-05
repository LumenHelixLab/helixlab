"""LLMAdapter base — the neutral-schema boundary (spec §5.2, invariant 2).

Provider SDK imports live ONLY in concrete adapters. Nothing outside
app/llm_adapters may import a provider SDK.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, tools: list[dict], **kwargs: Any) -> Any:
        """Send prompt with tools, return provider-specific raw response."""

    @abstractmethod
    def parse_response(self, raw_response: Any) -> dict[str, Any]:
        """Convert provider raw response to neutral LLMResponse:
        {text, tool_calls: [{name, arguments}], finish_reason}."""

    @abstractmethod
    def convert_tool_schema(self, neutral_tool: dict[str, Any]) -> dict[str, Any]:
        """Convert neutral tool schema to provider format."""

    @staticmethod
    def _decode_arguments(raw_arguments: Any) -> dict[str, Any]:
        """OpenAI-family providers hand back a JSON string; normalize."""
        if isinstance(raw_arguments, str):
            return json.loads(raw_arguments or "{}")
        return dict(raw_arguments or {})