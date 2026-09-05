"""Celery application (spec §4.4). Redis broker + result backend; heavy
computations run in dedicated queues; results cached by input hash."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

celery_app = Celery("helixlab", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_default_queue="compute",
    task_queues={"compute": {}},  # heavy engines add dedicated queues here
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    include=["services.worker_manager.app.tasks"],
)


def cache_key(task_name: str, payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True).encode("utf-8")
    return f"helixlab:cache:{task_name}:{hashlib.sha256(blob).hexdigest()}"


def cache_get(task_name: str, payload: dict[str, Any]) -> tuple[bool, Any]:
    """Returns (hit, value). Value is None when missed."""
    import redis

    client = redis.Redis.from_url(REDIS_URL)
    hit = client.get(cache_key(task_name, payload))
    return (True, json.loads(hit)) if hit is not None else (False, None)


def cache_set(task_name: str, payload: dict[str, Any], value: Any, ttl_seconds: int = 3600) -> None:
    import redis

    client = redis.Redis.from_url(REDIS_URL)
    client.set(cache_key(task_name, payload), json.dumps(value), ex=ttl_seconds)