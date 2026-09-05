"""Lab Spec parsing and execution DAG (spec §4.3).

The Orchestrator speaks only neutral schemas — no SDK imports here
(invariant 1/2).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"
_PARAM_RE = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")


@dataclass
class Node:
    id: str
    type: str  # compute | literature | visualization | logic
    raw: dict[str, Any]
    depends_on: list[str] = field(default_factory=list)


@dataclass
class NodeResult:
    node_id: str
    success: bool
    output: Any = None
    error: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }


class LabSpecValidationError(ValueError):
    """Raised when a Lab Spec fails JSON-Schema validation (invariant 5)."""


class LabSpecParser:
    """Validates a Lab Spec against schemas/lab-spec.schema.json and compiles
    the execution DAG."""

    def __init__(self) -> None:
        schema_path = SCHEMAS_DIR / "lab-spec.schema.json"
        self._schema = json.loads(schema_path.read_text(encoding="utf-8"))

    def parse(self, spec_json: dict[str, Any]) -> "ExecutionDAG":
        import jsonschema

        try:
            jsonschema.validate(spec_json, self._schema)
        except jsonschema.ValidationError as exc:
            raise LabSpecValidationError(f"Lab Spec invalid: {exc.message}") from exc

        # Compile depends_on edges. Undeclared nodes are still deterministically
        # ordered: Kahn's algorithm breaks ties by declaration order (FIFO).
        nodes: list[Node] = []
        for raw in spec_json["nodes"]:
            deps = list(raw.get("depends_on", []))
            if raw.get("data_ref"):
                ref = raw["data_ref"].split(".")[0]
                if ref not in deps:
                    deps.append(ref)
            nodes.append(Node(id=raw["id"], type=raw["type"], raw=raw, depends_on=deps))
        return ExecutionDAG(nodes)

    def substitute_parameters(self, spec_json: dict[str, Any]) -> dict[str, Any]:
        """Replace {{parameter}} placeholders with typed defaults (invariant 7).

        A string that is exactly one placeholder resolves to the parameter's
        typed value (so numeric params stay numeric in `params` objects); a
        placeholder embedded in a longer template is substituted as text.
        """
        params = {p["name"]: p["default"] for p in spec_json.get("parameters", [])}

        def resolve(name: str) -> Any:
            if name not in params:
                raise LabSpecValidationError(f"Unknown parameter: {name}")
            return params[name]

        def walk(value: Any) -> Any:
            if isinstance(value, str):
                whole = _PARAM_RE.fullmatch(value)
                if whole:
                    return resolve(whole.group(1))

                def repl(match: re.Match[str]) -> str:
                    return str(resolve(match.group(1)))

                return _PARAM_RE.sub(repl, value)
            if isinstance(value, list):
                return [walk(v) for v in value]
            if isinstance(value, dict):
                return {k: walk(v) for k, v in value.items()}
            return value

        return walk(spec_json)


class ExecutionDAG:
    def __init__(self, nodes: list[Node]) -> None:
        self.nodes = nodes

    def topological_sort(self) -> list[Node]:
        """Kahn's algorithm (FIFO tie-breaking = declaration order); raises on
        duplicate ids, dangling dependencies, or cycles."""
        by_id = {n.id: n for n in self.nodes}
        if len(by_id) != len(self.nodes):
            dupes = sorted({n.id for n in self.nodes} - set(n.id for n in by_id.values()))
            raise ValueError(f"Duplicate node id(s): {', '.join(dupes) or 'unknown'}")
        for n in self.nodes:
            for dep in n.depends_on:
                if dep not in by_id:
                    raise ValueError(f"Node {n.id!r} depends on unknown node {dep!r}")

        indegree = {n.id: 0 for n in self.nodes}
        children: dict[str, list[str]] = {n.id: [] for n in self.nodes}
        for n in self.nodes:
            for dep in n.depends_on:
                indegree[n.id] += 1
                children[dep].append(n.id)

        ready = [nid for nid, deg in indegree.items() if deg == 0]
        order: list[Node] = []
        while ready:
            node_id = ready.pop(0)  # FIFO → deterministic, declaration-ordered ties
            order.append(by_id[node_id])
            for child in children[node_id]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        if len(order) != len(self.nodes):
            raise ValueError("Lab Spec DAG contains a cycle")
        return order