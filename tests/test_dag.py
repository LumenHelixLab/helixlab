"""Unit tests for DAG compilation + preset validation (spec §9)."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from services.orchestrator.app.dag import ExecutionDAG, LabSpecParser, LabSpecValidationError, Node

PRESETS_DIR = Path(__file__).resolve().parents[1] / "presets"


def _spec(nodes, parameters=None):
    spec = {"id": "test-lab", "name": "Test Lab", "nodes": nodes}
    if parameters:
        spec["parameters"] = parameters
    return spec


def test_topological_sort_respects_dependencies():
    nodes = [
        Node("c", "compute", {}, ["b"]),
        Node("a", "compute", {}),
        Node("b", "literature", {}, ["a"]),
    ]
    dag = ExecutionDAG(nodes)
    order = [n.id for n in dag.topological_sort()]
    assert order.index("a") < order.index("b") < order.index("c")


def test_cycle_raises():
    nodes = [
        Node("a", "compute", {}, ["b"]),
        Node("b", "compute", {}, ["a"]),
    ]
    with pytest.raises(ValueError, match="cycle"):
        ExecutionDAG(nodes).topological_sort()


def test_dangling_dependency_raises():
    dag = ExecutionDAG([Node("a", "compute", {}, ["ghost"])])
    with pytest.raises(ValueError, match="unknown node"):
        dag.topological_sort()


def test_spec_validation_rejects_bad_type():
    parser = LabSpecParser()
    with pytest.raises(Exception):
        parser.parse(_spec([{"id": "x", "type": "not-a-type"}]))


def test_parameter_substitution():
    parser = LabSpecParser()
    spec = _spec(
        [{"id": "n", "type": "compute", "engine": "sage", "code_template": "genus({{g}})"}],
        parameters=[{"name": "g", "type": "integer", "default": 3}],
    )
    out = parser.substitute_parameters(spec)
    assert out["nodes"][0]["code_template"] == "genus(3)"


def test_unknown_parameter_raises():
    parser = LabSpecParser()
    spec = _spec([{"id": "n", "type": "compute", "engine": "sage", "code_template": "{{missing}}"}])
    with pytest.raises(Exception, match="Unknown parameter"):
        parser.substitute_parameters(spec)


def test_data_ref_implies_dependency():
    parser = LabSpecParser()
    dag = parser.parse(
        _spec([
            {"id": "src", "type": "compute", "engine": "sage", "code_template": "1"},
            {"id": "plot", "type": "visualization", "chart": "c", "data_ref": "src.output"},
        ])
    )
    plot = next(n for n in dag.nodes if n.id == "plot")
    assert "src" in plot.depends_on


def test_duplicate_node_ids_raise():
    dag = ExecutionDAG([Node("a", "compute", {}), Node("a", "compute", {})])
    with pytest.raises(ValueError, match="Duplicate node id"):
        dag.topological_sort()


def test_declared_order_tie_break_is_deterministic():
    dag = ExecutionDAG([Node("b", "compute", {}), Node("a", "compute", {})])
    order = [n.id for n in dag.topological_sort()]
    assert order == ["b", "a"]  # declaration order on ties, not reverse


def test_all_shipped_presets_validate():
    """Every preset in presets/ must pass the repo's own Lab Spec schema."""
    parser = LabSpecParser()
    preset_paths = sorted(PRESETS_DIR.glob("*.json"))
    assert preset_paths, "presets directory must not be empty"
    for path in preset_paths:
        raw = json.loads(path.read_text(encoding="utf-8"))
        parser.parse(raw)  # raises LabSpecValidationError on failure


def test_typed_parameter_substitution_in_params():
    parser = LabSpecParser()
    spec = _spec(
        [{"id": "s", "type": "compute", "engine": "qiskit",
          "params": {"rate": "{{error_rate}}"}, "code_template": "run"}],
        parameters=[{"name": "error_rate", "type": "float", "default": 0.01}],
    )
    out = parser.substitute_parameters(spec)
    assert out["nodes"][0]["params"]["rate"] == 0.01
    assert isinstance(out["nodes"][0]["params"]["rate"], float)