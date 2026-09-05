"""HESOT — Feedback & Training Service (spec §4.5).

Collects interaction logs, clusters error patterns, and emits PROMPT UPDATE
PROPOSALS. Proposals are never auto-applied: the human-review gate is on by
default (spec §13 open question 4 — invariant 6).
"""
from __future__ import annotations

import os
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

_scheduler = BackgroundScheduler()


def collect_and_cluster() -> int:
    """Daily job: cluster error patterns → emit proposals → invalidate caches
    tied to erroneous outputs. Returns the number of proposals created."""
    # Sprint 1: implement clustering (GAP timeouts on large groups, etc.).
    return 0


def _daily_job() -> None:
    collect_and_cluster()


def main() -> None:
    _scheduler.add_job(_daily_job, "cron", hour=3)
    _scheduler.start()
    print(f"[hesot] proposal-only feedback loop started at {datetime.now(timezone.utc).isoformat()}")
    try:
        import signal

        signal.pause()  # Windows dev: Ctrl+C exits
    except (AttributeError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()