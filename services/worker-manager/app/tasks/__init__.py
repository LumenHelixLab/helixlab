"""Engine plugin tasks (spec §4.4). Each runs its engine inside the sandbox
image (docker/sandbox.dockerfile): no network, cgroup CPU/memory limits,
writes confined to a temp dir (invariant 3).

Node result contract (invariant 6): {success: bool, output: Any,
error: {code, message}}.
"""
from __future__ import annotations

from typing import Any

from ..celery_app import cached, celery_app


def _run_engine(engine: str, code: str, timeout_seconds: int = 30) -> dict[str, Any]:
    """Common sandboxed execution path. In the prototype the engine containers
    are invoked via `docker run --rm --network none --memory --cpus`; wired to
    real engines in sprint 1 (spec §13.2 pins versions)."""
    hit, value = cached(f"run_{engine}", {"code": code})
    if hit:
        return {"success": True, "output": value, "error": {}}
    # Prototype placeholder: sandbox execution is wired in sprint 1.
    return {
        "success": False,
        "output": None,
        "error": {
            "code": "engine_not_wired",
            "message": f"{engine} sandbox execution lands in sprint 1 (see docs/REPO-SPEC.md next actions).",
        },
    }


@celery_app.task(name="run_wolfram")
def run_wolfram(code: str) -> dict[str, Any]:
    return _run_engine("wolfram", code)


@celery_app.task(name="run_gap")
def run_gap(code: str) -> dict[str, Any]:
    return _run_engine("gap", code)


@celery_app.task(name="run_sage")
def run_sage(code: str) -> dict[str, Any]:
    return _run_engine("sage", code)


@celery_app.task(name="run_qiskit")
def run_qiskit(circuit_json: str) -> dict[str, Any]:
    return _run_engine("qiskit", circuit_json)