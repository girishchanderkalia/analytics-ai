# AGENTS.md — Analytics Investigation Agent (POC)

## 1. Purpose

This repository implements an Analytics Investigation Agent used to evaluate an AI-driven
interaction model for Analytics Foundation. The agent helps users investigate KPI trends,
identify outliers, and perform wafer-level deep-dive analysis using existing Analytics
Foundation services.

- The agent does not own business semantics. Business semantics are defined by the application.
- Analytics Foundation provides deterministic services; it does not interpret business meaning.

## 2. Authoritative architecture reference

The target system architecture is defined in
[agentWorkflows/mcp-oss-target-architecture.puml](../agentWorkflows/mcp-oss-target-architecture.puml).
Treat this diagram as the source of truth for component boundaries, ownership, and allowed
call paths. Any code change must keep the system aligned with it. Key boundaries it encodes:

- **Application UI / BFF** owns HTTP endpoints, display routes, and both traditional and
  conversational views. It may call the Query Engine API directly for plain display
  (`GET /trends`) with no agent or MCP involvement.
- **Agent Runtime Framework** (LangGraph StateGraph + PydanticAI application agent) owns
  intent → `DetectionScope` and evidence → `FindingsSummary` only. It has no direct API,
  database, credential, checkpoint, or audit access.
- **MCP Capability Adaptor** is the only path from the agent runtime to Foundation APIs
  (Assets, Workspace, Query Engine, Processing). It exposes typed, validated,
  policy-governed tools — never a raw passthrough.
- **Model Gateway** is the only path to AI models. Agent code must not call model providers
  directly.
- **Session Manager** records model/tool/finding events and request/evidence/decision events
  into PostgreSQL, kept separate from LangGraph checkpoints.
- **Foundation Service APIs** (`apis/api.yml`, `apis/qe_api.yml`) are the only sanctioned entry
  points into PostgreSQL/StarRocks analytical data.

### 2.1 Language boundary

The system is a deliberate two-language split, not a single-language target:

- **Python owns the workflow runtime**: LangGraph orchestration, the PydanticAI
  application agent, the MCP capability adaptor, and interrupt/resume handling.
  Python has no app-facing HTTP surface of its own in the target state.
- **Java owns the app and API façade**: the UI shell, the BFF/REST layer the app
  talks to, and the stable service interfaces in `## 8`. Java never calls model
  providers, Foundation APIs, or PostgreSQL/StarRocks directly — it calls the
  Python workflow runtime.
- **Shared contracts** are the only thing both languages depend on for model,
  session, and foundation access, so neither side reimplements the other's
  types by hand. See `### 3.5 Shared contracts`.

## 3. Migration rules

### 3.1 Architecture boundary

Keep the architecture aligned to the target design in
`agentWorkflows/mcp-oss-target-architecture.puml`.

#### Keep in Python
- LangGraph workflow orchestration.
- Typed application agents and structured outputs.
- MCP tool adapters and tool contract enforcement.
- Human approval interrupts and resume flow.
- Workflow runtime state transitions and audit/event capture.

#### Keep in Java
- UI shell and app-facing API layer.
- BFF / REST façade.
- Mock Analytics Foundation services for local demo and testing.
- Service façade code that exposes stable business APIs to the app.

#### Keep in the application layer
- KPI definitions, dashboard semantics, and trend interpretation.
- Investigation workflow semantics.
- Outlier detection logic and evidence interpretation.
- Business-specific rules, filters, and domain model definitions.

#### Keep in the foundation layer
- Model gateway integration.
- Session, memory, and audit persistence.
- Capability/tool governance.
- Platform API integration and deterministic service calls.

### 3.2 Guardrails
- Do not move business semantics into `AnalyticsFoundation/`.
- Do not replace LangGraph with a Java workflow engine unless there is a clear, verified reason.
- Do not treat FastAPI itself as the blocker; REST is portable across languages.
- Treat MCP as the governance boundary for Analytics Foundation access, not as a simple REST wrapper.
- Keep workflow approval gates in the Python runtime.
- Use PostgreSQL as the eventual runtime state store for checkpoints and session evidence.
- Do not let Java call the model gateway, MCP tools, or PostgreSQL/StarRocks directly; it
  must go through the Python workflow runtime's API, using the shared contracts.
- Do not let the shared contracts drift: a field added to a Python model/session/foundation
  type must be reflected in the shared contract before the Java side depends on it.

### 3.3 Implementation order
1. Normalize the application agent layer.
2. Move runtime state to PostgreSQL.
3. Introduce the MCP capability layer.
4. Retire legacy custom capability plumbing.
5. Split the BFF/API façade into Java, calling the Python workflow runtime over a
   contract-defined API instead of being implemented in Python.

### 3.5 Shared contracts

Model, session, and foundation access are cross-language boundaries, so their
shapes are defined once and consumed by both sides instead of being hand-written
twice:

- **Model contracts** — `DetectionScope`, `FindingsSummary`, and any other typed
  agent input/output. Defined once (JSON Schema, generated from the Python
  Pydantic models) and consumed by Java as generated POJOs/DTOs.
- **Session contracts** — the session/event/evidence shapes recorded by the
  Session Manager (`agent_session_events`, `workspace_registrations`, `memory`)
  and returned by the workflow runtime's session/evidence endpoints.
- **Foundation access contracts** — the request/response shapes for the workflow
  runtime's own API (invoke investigation, resume, thread state, trends), which
  is what the Java façade actually calls; Java must not depend on Foundation's
  internal MCP tool schemas directly.
- Contracts live in one place both languages can generate from (e.g. an
  `contracts/` or `schemas/` folder with JSON Schema/OpenAPI), versioned with the
  code that defines them. Do not let Java redefine these types independently.

### 3.4 Reuse the current repo guidance
- The application owns business semantics.
- Analytics Foundation owns deterministic runtime capabilities.
- The current demonstrator can remain hybrid while the target architecture is phased in.

## 4. System model

### 4.1 Application-owned
The application owns:
- KPI definitions
- Dashboard semantics
- Context definitions
- Trend definitions
- Relevant datasets
- Relevant database tables
- Relevant parquet folders
- Business workflows

### 4.2 Analytics Foundation provided services
The platform provides:
- Workspace API (`apis/api.yml`)
- Query Engine Service API (`apis/qe_api.yml`)
- Processing API (`apis/api.yml`)
- PostgreSQL high-level KPI/context data
- StarRocks wafer-level analytical data

### 4.3 User interaction model
The user interacts using natural language, for example:
- Show me trends and outliers.
- Explain the most significant anomaly.
- Deep dive into the selected outlier.
- Compare affected wafers.
- Explain likely contributors.

The goal is to reduce manual navigation and make workflows conversational.

### 4.4 Investigation workflow

**Trend Analysis** — when the user asks "Show me trends and outliers":
- Query PostgreSQL trend/KPI data.
- Identify candidate outliers.
- Explain why outliers were detected.
- Suggest investigation scope.

Example output:
```
I found 3 significant outliers.

Most significant:
Machine: NXE3600
Product: A
Yield degradation: 15%

Would you like me to investigate this outlier?
```

**Deep Dive** — when the user asks "Deep dive into this outlier":
- Create workspace.
- Apply required filters.
- Register required datasets/tables.
- Wait for registration readiness.
- Query wafer-level data.
- Generate findings.
- Suggest follow-up analysis.

Always explain: which filters were applied, which datasets were used, and what evidence
supports the conclusion.

## 5. Operational rules

Never:
- Access HDFS directly.
- Access Object Store directly.
- Create StarRocks tables directly.
- Issue DDL statements directly.
- Bypass Analytics Foundation APIs.
- Invent datasets.
- Invent KPI definitions.

Always use Analytics Foundation services for deterministic actions.

## 6. Evidence requirements

Every recommendation must include supporting evidence.

Bad: "I think registration is still running."

Good:
```
Registration status is IN_PROGRESS.
Workspace: Yield_Investigation
Progress: 42%
Required table: wafer_yield
```

## 7. Response style

Prefer findings, evidence, and recommended next actions over long explanations. Be concise
and investigation-oriented.

## 8. Java service interfaces

These interfaces are the Java app/API façade's contract with the rest of the
system. Their request/response types must match the shared contracts in
`### 3.5`, not be redefined ad hoc; the façade calls the Python workflow runtime
to fulfill them rather than talking to Foundation APIs, MCP, or the model
gateway itself.

Implement these Java interfaces:

```java
public interface TrendService {
    TrendResponse getTrends();
}

public interface WorkspaceService {
    String createWorkspace();
    void addFilters(String workspaceId, Filters filters);
}

public interface RegistrationService {
    RegistrationStatus register(RegistrationRequest request);
}

public interface WaferDataService {
    WaferResult query(QueryRequest request);
}
```

## 9. Deployment

- Containerize with Docker. In the target (Java + Python) split, this is two images:
  one for the Java app/API façade, one for the Python FastAPI/uvicorn workflow
  runtime. The Java façade is the only one the app/UI talks to; it reaches the
  Python workflow runtime over its contract-defined API.
- Target Kubernetes cluster: reached only via SSH, no password required:
  `ssh fa-VCP@ics027036188.ics-eu-1.asml.com`.
- All workloads for this project are deployed into the `ai-agents` namespace. Do not deploy
  to `default` or any other namespace.
- Apply manifests through the SSH host (e.g. pipe manifests to
  `ssh fa-VCP@ics027036188.ics-eu-1.asml.com kubectl apply -n ai-agents -f -`, or copy them to
  the remote host first and run `kubectl apply -n ai-agents -f <file>`).