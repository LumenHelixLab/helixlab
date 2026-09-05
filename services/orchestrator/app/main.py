"""HelixLAB Orchestrator (FastAPI) — internal service behind the API Gateway.

Endpoints (internal contract, spec §3): parse Lab Specs, compile DAGs,
dispatch nodes via the tool dispatcher, merge results, generate memos.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from .dag import ExecutionDAG, LabSpecParser, LabSpecValidationError
from .llm_adapters.factory import LLMAdapterFactory

app = FastAPI(title="HelixLAB Orchestrator", version="0.1.0")

PRESETS_DIR = Path(__file__).resolve().parents[3] / "presets"


class LabSpecParserSingleton:
    _parser: LabSpecParser | None = None

    @classmethod
    def get(cls) -> LabSpecParser:
        if cls._parser is None:
            cls._parser = LabSpecParser()
        return cls._parser


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "orchestrator"}


@app.post("/dag/compile")
def compile_dag(spec: dict[str, Any]) -> dict[str, Any]:
    try:
        dag: ExecutionDAG = LabSpecParserSingleton.get().parse(spec)
    except LabSpecValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    order = [n.id for n in dag.topological_sort()]
    return {"ok": True, "execution_order": order}


@app.get("/presets")
def list_presets() -> dict[str, Any]:
    parser = LabSpecParserSingleton.get()
    presets = []
    for path in sorted(PRESETS_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        try:
            parser.parse(raw)  # presets are validated at load (invariant 5)
        except LabSpecValidationError as exc:
            raise HTTPException(status_code=500, detail=f"Invalid preset {path.name}: {exc}") from exc
        presets.append(raw)
    return {"ok": True, "presets": presets}


@app.post("/prompt/generate")
def generate_prompt(spec: dict[str, Any], provider: str = "anthropic") -> dict[str, Any]:
    """Compile a Lab Spec into a provider-routed prompt using the neutral
    tool schemas (spec §4.2 POST /api/prompt/generate)."""
    try:
        dag = LabSpecParserSingleton.get().parse(spec)
    except LabSpecValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tools = [_tool_schema_for(node) for node in dag.topological_sort()]
    if provider not in LLMAdapterFactory._adapters:
        raise HTTPException(status_code=422, detail=f"Unknown provider: {provider}")
    prompt = _spec_to_prompt(spec)
    return {"ok": True, "provider": provider, "prompt": prompt, "tools": tools}


def _tool_schema_for(node: Any) -> dict[str, Any]:
    """Neutral ToolSchema per DAG node type (invariant 2)."""
    if node.type == "compute":
        return {
            "name": f"{node.raw.get('engine', 'compute')}_evaluate",
            "description": f"Execute {node.type} node {node.id!r} on the {node.raw.get('engine')} engine.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string", "description": "Code to execute"}},
                "required": ["code"],
            },
        }
    if node.type == "literature":
        return {
            "name": "literature_search",
            "description": "Query a literature/evidence synthesis API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "question": {"type": "string"},
                },
            },
        }
    return {
        "name": f"{node.type}_node",
        "description": f"Execute {node.type} node {node.id!r}.",
        "parameters": {"type": "object", "properties": {}},
    }


def _spec_to_prompt(spec: dict[str, Any]) -> str:
    lines = [f"Lab: {spec.get('name', spec.get('id'))}"]
    if spec.get("description"):
        lines.append(spec["description"])
    lines.append("Nodes:")
    for node in spec["nodes"]:
        lines.append(f"- {node['id']} ({node['type']}): {node.get('engine') or node.get('source') or ''}")
    return "\n".join(lines)