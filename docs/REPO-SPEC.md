# Repo Spec — HelixLAB (187repo output contract)

*Captured 2026-09-04 via `/187repo` · operator: Chris Phillips / Lumen Helix Solutions*

## 1. Mode

`187repo repo` — local scaffold. No GitHub deploy (Power Mode requires an
explicit user-provided `GITHUB_PAT`; not supplied, and the request was for a
local repo).

## 2. Archetype / route

- **Archetype:** `--agent` family (Python FastAPI + RAG-style orchestration),
  extended to the spec's four-service layout (`--full`'s Next.js/tRPC/Prisma
  stack was rejected — the spec mandates FastAPI + Celery + Express + React).
- **Route chain:** `187repo` → `187web-ecosystem` (structure) +
  `187web-manifest` (discipline) + `helixlab` skill (spec contracts).

## 3. Commands run

```
git init -b main (D:\projects\helixlab)
New-Item service/schema/preset/docs directory tree
copy docs/helixlab-spec.md + .claude/skills/helixlab/ (project skill surface)
initial commits: contracts → services → 187 surface
```

## 4. Files created / changed

See repo tree at the scaffold commit: README, AGENTS.md, schemas/ (3 neutral
contracts + Lab Spec JSON Schema), presets/qec_ag_codes.json, four service
skeletons, frontend scaffold, docker sandbox + dev compose, tests/test_dag.py,
docs (spec + this file), project skill copy.

## 5. Next actions

1. `gh repo create LumenHelixLab/helixlab --private` + push (needs explicit go-ahead; Power Mode needs `GITHUB_PAT`).
2. Pin engine versions in Docker images (spec §13.2 — unresolved).
3. Decide orchestrator/worker-manager merge for the prototype (spec §13.1).
4. Implement Gemini adapter against the installed SDK (only stub shipped).
5. Wire CI: cross-LLM adapter matrix test + DAG unit tests + compose smoke.
6. Regional endpoint strategy for Kimi/Gemini (spec §13.3).

## Safety guardrails honored

- No GitHub deploy without explicit PAT/approval. ✔ (local only)
- No uptime/security/performance guarantees stated. ✔
- Public Pages content would require `187access-plus` + `187include` review.