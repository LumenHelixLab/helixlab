"""Engine plugin tasks (spec §4.4). Each engine runs inside the sandbox image
(docker/sandbox.dockerfile) launched with:
    docker run --rm --network none --memory 2g --cpus 2 --read-only --cap-drop ALL
Writes are confined to a mounted temp dir. Never weaken this (invariant 3).

Node result contract (invariant 6): {success: bool, output: Any,
error: {code, message}}.
"""
from __future__ import annotations

from typing import Any

from ..celery_app import cache_get, cache_set


def _run_engine(engine: str, code: str) -> dict[str, Any]:
    """Sandboxed execution with read-through caching (spec §4.4)."""
    hit, value = cache_get(f"run_{engine}", {"code": code})
    if hit:
        return {"success": True, "output": value, "error": {}}
    # Prototype placeholder: engine containers are wired in sprint 1
    # (versions pinned per spec §13.2). On success, cache the output:
    #   cache_set(f"run_{engine}", {"code": code}, output)
    return {
        "success": False,
        "output": None,
        "error": {
            "code": "engine_not_wired",
            "message": f"{engine} sandbox execution lands in sprint 1 (see docs/REPO-SPEC.md next actions).",
        },
    }


def _run_wolfram(code: str) -> dict[str, Any]:
    return _run_engine("wolfram", code)


def _run_gap(code: str) -> dict[str, Any]:
    return _run_engine("gap", code)


def _run_sage(code: str) -> dict[str, Any]:
    return _run_engine("sage", code)


def _run_qiskit(circuit_json: str) -> dict[str, Any]:
    return _run_engine("qiskit", circuit_json)


# Celery task registrations.
from ..celery_app import celery_app  # noqa: E402

run_wolfram = celery_app.task(name="run_wolfram")(_run_wolfram)
run_gap = celery_app.task(name="run_gap")(_run_gap)
run_sage = celery_app.task(name="run_sage")(_run_sage)
run_qiskit = celery_app.task(name="run_qiskit")(_run_qiskit)