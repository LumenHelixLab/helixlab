"""Moonshot Kimi adapter — OpenAI-compatible (spec §5.3)."""
from __future__ import annotations

from typing import Any

from .openai_adapter import OpenAIAdapter


class KimiAdapter(OpenAIAdapter):
    def __init__(self, api_key: str | None = None) -> None:
        import os

        super().__init__(
            api_key=api_key or os.getenv("MOONSHOT_API_KEY"),
            base_url="https://api.moonshot.cn/v1",
        )

    def generate(self, prompt: str, tools: list[dict], **kwargs: Any) -> Any:
        kwargs.setdefault("model", "moonshot-v1-8k")
        return super().generate(prompt, tools, **kwargs)