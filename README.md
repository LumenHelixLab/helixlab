# HelixLAB

> `/187repo` scaffold · archetype `--agent` (spec-driven multi-service) · local repo, no remote yet

Integrated AI research laboratory: topological vector mapping, quantum computing,
cryptography, algebraic geometry. Math engines (Wolfram, GAP, SageMath, Qiskit)
+ literature synthesis (SciSpace, Consensus) + a drag-and-drop lab builder +
provider-agnostic cross-LLM orchestration + a feedback-driven improvement loop.

**Full spec:** [`docs/helixlab-spec.md`](docs/helixlab-spec.md) — authoritative.
**Operating summary as a skill:** [`.claude/skills/helixlab/SKILL.md`](.claude/skills/helixlab/SKILL.md)
(also installed portfolio-wide at `skills/helixlab/` and user-wide for Claude/Codex/Grok).

## Architecture

```
frontend (React SPA: React Flow lab builder · Three.js viewer · feedback widget)
  → api-gateway (Node/Express: REST + WebSocket, JWT, rate limits, JSON-Schema)
    → orchestrator (Python/FastAPI: Lab Spec → DAG → dispatch → merge → memo)
      → worker-manager (Celery + Redis: engine plugin tasks, result caching)
      → feedback-hesot (interaction log → clustering → prompt-store proposals)
```

## Invariants (violating any of these is a bug)

1. Provider-agnostic core — no engine/LLM SDK imports outside adapter modules.
2. Neutral schemas are the contract — [`schemas/`](schemas/) is the boundary.
3. Sandboxing — engine code runs in Docker, no network, cgroup limits.
4. Secrets via environment variables only.
5. Every Lab Spec and input validated against JSON Schema.
6. Node results carry `{success, output, error}`; one retry; HESOT updates are
   proposals behind a human-review gate.
7. Deterministic artifacts — a run reproduces from (preset, parameters) alone.

## Quickstart (dev)

```powershell
# services
pnpm --dir services/api-gateway install
pnpm --dir services/api-gateway start            # gateway on :8080
pip install -r services/orchestrator/requirements.txt
uvicorn services.orchestrator.app.main:app --reload --port 8090
# workers + backing services
docker compose -f dev/docker-compose.yml up -d postgres redis
```

## Repo map

| Path | What |
|------|------|
| `services/api-gateway/` | Express REST + WebSocket, JWT, rate limits |
| `services/orchestrator/` | FastAPI: DAG compile, tool dispatch, report merge |
| `services/worker-manager/` | Celery tasks: `run_wolfram/gap/sage/qiskit` |
| `services/feedback-hesot/` | APScheduler feedback loop (human-gated) |
| `frontend/` | React 18 SPA (React Flow, R3F, MUI) — scaffold |
| `schemas/` | Neutral contracts: Lab Spec, ToolSchema, LLMResponse |
| `presets/` | Ready-to-run Lab Specs (`{{parameter}}` substitution) |
| `docker/` | Sandbox image (no network, non-root, cgroup-limited) |
| `dev/` | Local compose: postgres + redis |

## 187 routing

Repo / install / deploy → `/187repo` (187WEB suite) · this repo was scaffolded
via `187repo` with the output contract captured in
[`docs/REPO-SPEC.md`](docs/REPO-SPEC.md).

## Status

Prototype scaffold (spec §12 gates pending). Performance budgets and testing
strategy live in the spec (§8, §9). No uptime, security, or performance
guarantees.