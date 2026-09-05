# Senior Engineer Handoff: Project HelixLAB

## 1. Introduction
This document provides a comprehensive engineering handoff for **HelixLAB**, an integrated AI research laboratory specializing in topological vector mapping, quantum computing, cryptography, and complex algebraic geometry. It is intended for a senior engineering team tasked with implementation, refinement, or integration with external systems (e.g., grok, claude, kimi, gemini, chatgpt). The content is written at a depth sufficient for immediate development start.

The previous high-level summary has been expanded into precise component specifications, API contracts, data schemas, security considerations, performance budgets, and a phased delivery plan. All design decisions are justified based on scalability, extensibility, and research-grade reliability.

## 2. System Context and Goals

**Primary Goal:** Provide researchers with a unified, web-accessible environment that combines:
- Multiple computational mathematics engines (Wolfram, GAP, SageMath, etc.)
- Literature and evidence synthesis APIs (SciSpace, Consensus)
- Interactive visualization (Three.js, D3.js)
- Modular lab construction via drag-and-drop GUI
- Cross-LLM prompt generation and execution
- Continuous learning through user feedback (HESOT)

**Target Users:** Postgraduate researchers, cryptography engineers, algebraic geometers, quantum computing theorists.

**Deployment Model:** Microservices running in Docker containers, orchestrated by Kubernetes in production. The core system is provider-agnostic for LLMs and math engines.

## 3. High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     Frontend (React SPA)                      │
│  Lab Builder (React Flow) · 3D Viewer (Three.js) · Feedback   │
└─────────┬─────────────────┬────────────────────┬─────────────┘
          │        WebSocket / REST              │
┌─────────▼─────────────────▼────────────────────▼─────────────┐
│                    API Gateway (Node.js)                      │
│  Express REST · WebSocket · JWT auth · rate limiting ·        │
│  JSON-Schema validation                                       │
└─────────┬─────────────────┬────────────────────┬─────────────┘
┌─────────▼─────────┐ ┌─────▼─────────────┐ ┌────▼──────────────┐
│ Orchestrator      │ │ Worker Manager    │ │ Feedback &        │
│ (Python/FastAPI)  │ │ (Celery + Redis)  │ │ Training (HESOT)  │
└─────────┬─────────┘ └─────┬─────────────┘ └────┬──────────────┘
┌─────────▼─────────────────▼────────────────────▼──────────────┐
│  External Services Adapters                                   │
│  Math engines: Wolfram, GAP, SageMath, Qiskit                 │
│  Literature APIs: SciSpace, Consensus, Semantic Scholar       │
│  LLM providers: OpenAI, Anthropic, Google, Moonshot, Llama    │
└───────────────────────────────────────────────────────────────┘
```

**Service Communication:**
- Frontend ↔ API Gateway: REST for CRUD; WebSocket for streaming.
- API Gateway ↔ Orchestrator: gRPC or REST (internal).
- Orchestrator ↔ Worker Manager: Celery message queue (Redis broker).
- Worker Manager ↔ External Engines: direct subprocess (local) or HTTP (cloud).
- Feedback Service ↔ Orchestrator: shared PostgreSQL + event bus.

## 4. Component Specifications

### 4.1 Frontend (React + TypeScript)
**Core Libraries:** React 18, TypeScript 5, Zustand, React Flow, Three.js via React Three Fiber, D3.js, Material-UI v5, Socket.IO.

**Key Features:**
- **Lab Builder:** drag module nodes from a palette, connect, configure via property panel; canvas maintains a JSON DAG.
- **3D Viewer:** renders mathematical objects (curves, braids, graphs); camera controls, parameter-driven updates.
- **Feedback Widget:** thumbs up/down, comments, user edits — embedded in every result panel.
- **Run Panel:** progress, logs, partial results streamed via WebSocket.

**Component Library:** `ModuleNode`, `PlotPanel`, `ThreeCanvas`, `CitationList`.

### 4.2 API Gateway (Node.js + Express)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/lab/spec` | Validate and store a Lab Spec JSON. Returns `lab_id`. |
| GET | `/api/lab/spec/:id` | Retrieve Lab Spec. |
| POST | `/api/lab/run` | Start execution of a Lab Spec. Returns `run_id`. |
| GET | `/api/lab/run/:id/status` | Get current status (queued, running, completed, failed). |
| POST | `/api/feedback` | Submit user feedback for a result. |
| GET | `/api/presets` | List available presets. |
| POST | `/api/prompt/generate` | Generate LLM prompt from a Lab Spec. |

**WebSocket Events:** `run.update` (partial results, logs, progress), `run.complete` (final output + citations), `run.error`.

**Auth:** JWT-based; roles admin/researcher. **Rate limiting:** per user/IP via express-rate-limit.

### 4.3 Orchestrator (Python, FastAPI)
Responsibilities: parse Lab Spec into an execution DAG; dispatch nodes to plugins; manage tool adapters (LLM + engine); merge results from computation and literature; generate the final research memo.

```python
class LabSpecParser:
    def parse(spec_json: dict) -> ExecutionDAG: ...

class ExecutionDAG:
    nodes: list[Node]
    edges: list[Edge]
    def topological_sort() -> list[Node]: ...

class ToolDispatcher:
    def run_node(node: Node, context: dict) -> NodeResult: ...

class LLMAdapterManager:
    def get_adapter(provider: str) -> LLMAdapter: ...

class ReportGenerator:
    def generate(dag_results: dict, citations: list) -> str: ...
```

**DAG Node Types:** `compute` (runs code on an engine), `literature` (queries an external API), `visualization` (generates data for frontend rendering), `logic` (conditionals/loops).

**Error Handling:** each node returns `{success, output, error}`; one retry per failed node; the run is marked failed if a critical node fails.

### 4.4 Worker Manager (Celery)
Celery + Redis (broker and result backend). Each engine plugin is a Celery task: `run_wolfram(code)`, `run_gap(code)`, `run_sage(code)`, `run_qiskit(circuit_json)`, etc. Workers scale horizontally; heavy computations run in dedicated queues. Results cached in Redis with TTL keyed on input hash.

### 4.5 Feedback & Training Service (HESOT)
Logs all interactions and periodically improves the system.

```
interaction_log:
  id, timestamp, user_id, lab_spec_id, node_id, result_id,
  feedback_type, comment, edited_output
```

**Training loop (prototype):** collect logs daily → cluster common error patterns (e.g., GAP timeouts on large groups) → update prompt templates in the Orchestrator's prompt store (PostgreSQL) → invalidate cache entries tied to erroneous outputs → optionally fine-tune a small tool-selection classifier. Implemented with APScheduler.

## 5. Cross-LLM Adapter Framework

### 5.1 Neutral Schemas
```python
# ToolSchema
{
  "name": "gap_evaluate",
  "description": "Evaluate GAP code and return result.",
  "parameters": {
    "type": "object",
    "properties": {"code": {"type": "string", "description": "GAP code to execute"}},
    "required": ["code"]
  }
}

# LLMResponse
{
  "text": "optional text",
  "tool_calls": [{"name": "gap_evaluate", "arguments": {"code": "Order(SymmetricGroup(5));"}}],
  "finish_reason": "tool_calls"
}
```

### 5.2 Adapter Interface
```python
class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, tools: list[dict], **kwargs) -> dict:
        """Send prompt with tools, return provider-specific raw response."""
    @abstractmethod
    def parse_response(self, raw_response: Any) -> dict:
        """Convert provider raw response to neutral LLMResponse."""
    @abstractmethod
    def convert_tool_schema(self, neutral_tool: dict) -> dict:
        """Convert neutral tool schema to provider format."""
```

### 5.3 Provider Implementations

**OpenAI** — `tools=[{"type": "function", "function": t}]`, `tool_choice="auto"`; parse `raw["choices"][0]["message"]` → `tool_calls[].function.name/arguments` (JSON-decode arguments). Tool schema: neutral parameters nested under `function`.

**Anthropic Claude** — `client.messages.create(model, max_tokens=4096, system=..., messages=[...], tools=...)`; parse `raw.content` blocks: `type=="text"` → text, `type=="tool_use"` → `{name, input}`; `finish_reason = raw.stop_reason`. Tool schema: `{name, description, input_schema}`.

**Google Gemini** — `genai.GenerativeModel(model_name, tools=[{"function_declarations": [...]}])`, `model.generate_content(prompt)`; parsing depends on SDK version.

**Moonshot Kimi** — OpenAI-compatible: `openai.OpenAI(api_key=MOONSHOT_API_KEY, base_url="https://api.moonshot.cn/v1")`, model `moonshot-v1-8k`; same parse as OpenAI.

**Llama 3** — via Together: `base_url="https://api.together.xyz/v1"`, model `meta-llama/Llama-3-70b-chat-hf`; same parse as OpenAI.

**Factory:** `LLMAdapterFactory._adapters = {"openai": ..., "anthropic": ..., "google": ..., "moonshot": ..., "llama": ...}`; `get_adapter(provider)` raises on unknown provider.

### 5.4 Fallback Mode
If a provider lacks function calling (or text-only is chosen), the Orchestrator parses the LLM's text output for patterns like `gap_evaluate("...")` and executes them.

## 6. Presets Specification
Each preset is a JSON file defining a default Lab Spec with pre-configured nodes. Example — "Quantum Error Correction from AG Codes":

```json
{
  "id": "qec_ag_codes",
  "name": "Quantum Error Correction from AG Codes",
  "description": "Construct quantum CSS codes from algebraic curves and simulate performance.",
  "nodes": [
    {"id": "curve", "type": "compute", "engine": "sage", "code_template": "C = curves.genus({{genus}}).random({{field}})"},
    {"id": "code", "type": "compute", "engine": "sage", "code_template": "GoppaCode(C)"},
    {"id": "simulate", "type": "compute", "engine": "qiskit", "params": {"error_model": "depolarizing", "rate": "{{error_rate}}"}},
    {"id": "literature", "type": "literature", "source": "scispace", "query": "quantum codes from algebraic curves"},
    {"id": "consensus", "type": "literature", "source": "consensus", "question": "Are algebraic geometry codes competitive with toric codes?"},
    {"id": "plot", "type": "visualization", "chart": "error_rate_curve", "data_ref": "simulate.output"}
  ],
  "parameters": [
    {"name": "genus", "type": "integer", "default": 3},
    {"name": "field", "type": "integer", "default": 7},
    {"name": "error_rate", "type": "float", "default": 0.01}
  ]
}
```

The Orchestrator substitutes `{{parameter}}` placeholders before execution.

## 7. Security and Sandboxing
- All engine code runs inside Docker containers with **no network access** (except explicitly allowed APIs).
- CPU and memory limits enforced via cgroups.
- User-supplied code is wrapped to prevent filesystem writes outside a temp directory.
- API keys stored in environment variables, never in code or logs.
- JWT tokens expire and are validated on every request.
- Input validation against JSON Schemas to prevent injection.

## 8. Performance Budgets

| Operation | Target Latency |
|-----------|----------------|
| Lab Spec validation | < 100 ms |
| Simple compute node (Wolfram `1+1`) | < 2 s |
| GAP group order (small) | < 3 s |
| Literature search (SciSpace) | < 2 s |
| WebSocket push of partial result | < 500 ms |
| Full lab run (10 nodes, moderate) | < 60 s (async) |

Caching reduces repeated computations to < 50 ms.

## 9. Testing Strategy
- **Unit:** adapter conversion (neutral ↔ provider); DAG topological sort; engine plugin wrappers.
- **Integration:** Orchestrator with mock engines; API Gateway with fake LLM adapter; feedback logging.
- **End-to-End (CI):** run a simple Lab Spec through the full stack; cross-LLM test — generate a prompt per provider and verify tool-call formatting.
- **Performance:** load test WebSocket with 100 concurrent users.

## 10. Deployment
Production: Kubernetes (EKS/GKE); services — API Gateway (Node), Orchestrator (Python), Celery workers, Redis, PostgreSQL; engine containers `wolfram-engine`, `gap`, `sage`, `qiskit` as separate pods; frontend via CDN. CI/CD: GitHub Actions → build Docker images → push to registry → helm upgrade.

## 11. Documentation Requirements
User Guide (Lab Builder, presets, feedback) · Developer Guide (architecture, adding engine plugins and LLM adapters) · API Reference (OpenAPI/Swagger) · Prompt Engineering Guide (cross-LLM prompts).

## 12. Next 5 Upgrade Gates (Technical Detail)
1. **Formal Verification Integration** — Lean 4 worker + API; LLM-assisted auto-formalization of simple theorems; verify group cohomology and code parameters in CI.
2. **Distributed Collaboration** — CRDTs for concurrent lab editing; WebRTC presence; shared versioned prompt store.
3. **Advanced Visualization & XR** — WebXR via Three.js; GPU-accelerated graph layout (WebGL); Apache Arrow streaming.
4. **Autonomous Research Agent** — RL for tool selection; arXiv submission API integration; safe execution policies for long-running experiments.
5. **Commercial SaaS** — Stripe billing; multi-tenant isolation; marketplace for third-party presets/adapters.

## 13. Open Questions for Refinement
1. Should the Orchestrator and Worker Manager be merged for the prototype?
2. Which versions of SageMath, GAP, and Wolfram Engine to pin in Docker images?
3. How to handle LLM providers requiring regional API endpoints (Kimi, Gemini)?
4. What is the acceptable threshold for HESOT automatic prompt updates without human review?
5. Should the prototype support user-uploaded code for custom engine plugins?