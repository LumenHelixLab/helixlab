---
name: helixlab
description: >
  Design, build, and integrate with HelixLAB — the provider-agnostic AI research
  lab stack (math engines + literature APIs + cross-LLM tool-calling adapters +
  HESOT feedback loop). Use when creating or editing HelixLAB services, Lab Specs,
  presets, LLM adapters, engine plugins, DAG orchestration, or sandboxing; when
  writing cross-LLM tool-calling code for OpenAI/Anthropic/Gemini/Kimi/Llama; or
  whenever the user mentions HelixLAB, Lab Spec, presets, research-lab
  orchestration, or "cross-LLM".
---

# HelixLAB — cross-agent operational skill

You are helping with HelixLAB: an AI research laboratory combining math engines
(Wolfram, GAP, SageMath, Qiskit), literature APIs (SciSpace, Consensus,
Semantic Scholar), drag-and-drop lab composition, and provider-agnostic
cross-LLM orchestration with a feedback-driven improvement loop (HESOT).
This skill is written to be followed by ANY LLM agent (Claude, Codex, Kimi,
Gemini, Grok, ChatGPT) — the contracts below are the shared language.

**Full specification:** `reference/helixlab-spec.md` (in this skill's folder) —
read it before implementing or changing any contract. It is authoritative; this
file is the operating summary.

## Non-negotiable invariants (violating any of these is a bug)

1. **Provider-agnostic core.** No engine or LLM SDK imports outside adapter
   modules. The Orchestrator speaks only neutral schemas.
2. **Neutral schemas are the contract.** `ToolSchema` (name, description,
   JSON-Schema parameters) in; `LLMResponse` ({text, tool_calls[{name,
   arguments}], finish_reason}) out. Never leak provider shapes past the
   adapter boundary.
3. **Sandboxing.** Engine code runs in Docker with NO network (except
   explicitly allowed APIs), cgroup CPU/memory limits, writes confined to a
   temp dir. Never weaken this for convenience.
4. **Secrets.** API keys via environment variables only — never in code,
   prompts, logs, or Lab Specs.
5. **Validation.** Every Lab Spec and every external input is validated against
   JSON Schema before use (injection defense).
6. **Claim discipline.** Every node result carries `{success, output, error}`
   — `success` a boolean flag, `error` a structured payload; one retry, then
   fail the run if the node is critical. HESOT updates are proposals until
   thresholds are met — never auto-apply prompt changes without the configured
   review gate (spec section 13, open question 4 — unresolved: default to
   requiring review).
7. **Deterministic artifacts.** Presets substitute `{{parameter}}` placeholders
   before execution; parameters are typed and defaulted in the preset; a run
   must be reproducible from (preset, parameters) alone.

## Architecture snapshot

```
Frontend (React SPA: React Flow lab builder, Three.js viewer, feedback widget)
  → API Gateway (Node/Express: REST + WebSocket, JWT, rate limits, JSON-Schema)
    → Orchestrator (Python/FastAPI: Lab Spec → DAG → dispatch → merge → memo)
      → Worker Manager (Celery + Redis: engine plugin tasks, result caching)
        → Adapters (math engines · literature APIs · LLM providers)
    → Feedback & Training (HESOT: interaction_log → clustering → prompt store)
```

Node types: `compute` | `literature` | `visualization` | `logic`.

## API Gateway contract

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/lab/spec` | Validate + store Lab Spec → `lab_id` |
| GET | `/api/lab/spec/:id` | Retrieve Lab Spec |
| POST | `/api/lab/run` | Execute Lab Spec → `run_id` |
| GET | `/api/lab/run/:id/status` | queued / running / completed / failed |
| POST | `/api/feedback` | Submit feedback on a result |
| GET | `/api/presets` | List presets |
| POST | `/api/prompt/generate` | Lab Spec → LLM prompt |

WebSocket events: `run.update` (progress/logs/partials), `run.complete`
(output + citations), `run.error`. Auth: JWT, roles `admin`/`researcher`.

## Cross-LLM adapter recipe (the critical pattern)

One `LLMAdapter` interface per provider — three methods each:
`generate(prompt, tools, **kwargs)`, `parse_response(raw) → LLMResponse`,
`convert_tool_schema(neutral_tool) → provider shape`.

| Provider | Tool schema shape | Parse notes |
|----------|-------------------|-------------|
| OpenAI | `{"type":"function","function":{name,description,parameters}}` | `choices[0].message.tool_calls[]`, JSON-decode `arguments` |
| Anthropic | `{name, description, input_schema}` | `content[]` blocks: `text` → text, `tool_use` → {name, input}; `stop_reason` |
| Gemini | `{"function_declarations":[...]}` | SDK-version-dependent — check installed SDK |
| Moonshot Kimi | OpenAI-compatible, `base_url=https://api.moonshot.cn/v1` | same as OpenAI, model `moonshot-v1-8k` |
| Llama (Together) | OpenAI-compatible, `base_url=https://api.together.xyz/v1` | same as OpenAI, model `meta-llama/Llama-3-70b-chat-hf` |

Factory: `LLMAdapterFactory.get_adapter(provider)` — unknown provider raises.
(The spec names this component `LLMAdapterManager` in §4.3 and
`LLMAdapterFactory` in §5.3 — same role; reconcile to one name when
implementing.) **Fallback mode:** when a provider lacks function calling, parse
tool calls out of the text (`tool_name("...")` patterns) before executing.

When adding a provider: implement the three methods, register in the factory,
add a cross-LLM test that asserts tool-call formatting for the new provider
alongside all existing ones (see Testing in the spec).

## Preset shape

```json
{
  "id": "kebab-id", "name": "...", "description": "...",
  "nodes": [{"id","type":"compute|literature|visualization|logic","engine"?,"source"?,"code_template"?,"params"?,"query"?,"question"?,"chart"?,"data_ref"?}],
  "parameters": [{"name","type","default"}]
}
```

`{{parameter}}` placeholders are substituted by the Orchestrator pre-run.
Parameterize every varying input — presets must never hardcode what a
parameter can express. Presets are JSON files loaded by the service (spec §6
defines the format; no preset-registration endpoint exists — `GET /api/presets`
only lists them).

## Performance budgets (design to these, test against these)

Spec validation < 100 ms · trivial compute node < 2 s · small GAP group order
< 3 s · literature search < 2 s · WebSocket partial-result push < 500 ms ·
10-node lab run < 60 s async · cache hit < 50 ms (Redis, TTL by input hash).

## Workflows

**Create a preset:** draft nodes per the shape above → parameterize → validate
against JSON Schema → test with the Orchestrator's mock engines → ship as a
JSON file per spec §6 (convention this skill adds: keep each node's output
traceable via `data_ref` where downstream nodes consume it).

**Add an engine plugin:** Celery task (`run_<engine>(code)`) in the Worker
Manager → dedicated queue for heavy runs → cache by input hash → Docker sandbox
per invariant 3 → unit test the wrapper + integration test through the
Orchestrator with mocks.

**Add an LLM provider:** follow the adapter recipe above; never bypass the
neutral schemas; test all providers in one matrix.

**HESOT loop:** interaction_log collection → error-pattern clustering → prompt
template updates (as proposals) → cache invalidation for erroneous outputs →
optional tool-selection classifier. Respect the human-review threshold
(invariant 6).

## Roadmap awareness (Gates 1-5)

Lean 4 formal verification · CRDT collaboration · WebXR/Arrow · autonomous
research agent (RL tool selection, arXiv submission) · commercial SaaS
(Stripe, multi-tenant, preset marketplace). When designing new features, place
them on this path and don't break forward compatibility — e.g. keep DAG node
schema extensible, keep prompt store versioned.

## Environment notes (this machine)

- Portfolio working copies and skills live under `D:\projects`; this skill's
  canonical copy is `D:\projects\skills\helixlab\`.
- Docker is the sandbox substrate; Postgres runs via `dev/docker-compose.yml`
  patterns in the lumenhelix repo when a DB is needed locally.
- pnpm for Node services; Python services use pinned requirements.