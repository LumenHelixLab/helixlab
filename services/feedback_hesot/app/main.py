"""HESOT — Feedback & Training Service (spec §4.5).

Collects interaction logs, clusters error patterns, and emits PROMPT UPDATE
PROPOSALS. Proposals are never auto-applied: the human-review gate is on by
default (spec §13 open question 4 — invariant 6).
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

INTERACTION_LOG_DDL = """
CREATE TABLE IF NOT EXISTS interaction_log (
  id            BIGSERIAL PRIMARY KEY,
  timestamp     TIMESTAMPTZ NOT NULL DEFAULT now(),
  user_id       TEXT NOT NULL,
  lab_spec_id   TEXT NOT NULL,
  node_id       TEXT NOT NULL,
  result_id     TEXT NOT NULL,
  feedback_type TEXT NOT NULL,          -- thumbs_up | thumbs_down | edit | comment
  comment       TEXT,
  edited_output JSONB
);
CREATE TABLE IF NOT EXISTS prompt_proposal (
  id          BIGSERIAL PRIMARY KEY,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  pattern     TEXT NOT NULL,
  proposal    JSONB NOT NULL,
  status      TEXT NOT NULL DEFAULT 'proposal'  -- proposal | approved | rejected
);
"""


def _ensure_schema() -> None:
    """Apply the interaction-log DDL at startup when a database is configured."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[hesot] DATABASE_URL unset — running without persistence (dev mode)")
        return
    try:
        import psycopg

        with psycopg.connect(database_url) as conn:
            conn.execute(INTERACTION_LOG_DDL)
        print("[hesot] interaction_log schema ensured")
    except Exception as exc:  # pragma: no cover - dev environments without PG
        print(f"[hesot] schema setup skipped: {exc}")


def collect_and_cluster() -> int:
    """Daily job: cluster error patterns → emit proposals → invalidate caches
    tied to erroneous outputs. Returns the number of proposals created."""
    # Sprint 1: implement clustering (GAP timeouts on large groups, etc.).
    return 0


def _daily_job() -> None:
    collect_and_cluster()


def main() -> None:
    _ensure_schema()
    scheduler = BackgroundScheduler()
    scheduler.add_job(_daily_job, "cron", hour=3)
    scheduler.start()
    print(f"[hesot] proposal-only feedback loop started at {datetime.now(timezone.utc).isoformat()}")
    threading.Event().wait()  # portable block (signal.pause is POSIX-only)


if __name__ == "__main__":
    main()