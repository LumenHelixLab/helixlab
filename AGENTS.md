# AGENTS.md — helixlab

Local repo scaffolded from `docs/helixlab-spec.md` (authoritative) via the
187repo convention. Branch: `main`. No remote yet — create
`LumenHelixLab/helixlab` when shipping.

## Commands

| Service | Command | Port |
|---------|---------|------|
| api-gateway | `pnpm --dir services/api-gateway install && pnpm --dir services/api-gateway start` | 8080 |
| orchestrator | `uvicorn services.orchestrator.app.main:app --reload --port 8090` | 8090 |
| worker_manager | `celery -A services.worker_manager.app.celery_app worker -Q compute -c 2` | — |
| feedback_hesot | `python -m services.feedback_hesot.app.main` | 8095 |
| backing services | `docker compose -f dev/docker-compose.yml up -d postgres redis` | 5432/6379 |
| tests | `python -m pytest tests/ -q` | — |

Prototype-known-limits (documented, not silently accepted): socket.io CORS is
`*` and rate limiting is global (not per-user) in the gateway — both tighten
before any deployment.

## Invariants

See `README.md` §Invariants and the skill copy at
`.claude/skills/helixlab/SKILL.md` (canonical portfolio copy:
`D:\projects\skills\helixlab\`). The skill is the cross-agent operating
contract; when it and this file disagree, the skill + spec win.

## Layout rules

- **Adapters are the only place SDKs may be imported** (`app/llm_adapters/*`,
  engine tasks in `services/worker-manager/app/tasks/*`).
- **Schemas in `schemas/` are versioned contracts.** Changing them requires a
  changelog entry and a migration note for stored Lab Specs.
- **Presets** are JSON files in `presets/` — validated at load; parameters
  typed + defaulted; `{{parameter}}` substitution happens in the orchestrator.
- **HESOT** writes proposals only; the human-review gate is on by default
  (spec §13, open question 4 unresolved).
- Python services: pinned `requirements.txt` per service. Node: pnpm.

## Session close convention

Update this file when structure, contracts, or commands change.