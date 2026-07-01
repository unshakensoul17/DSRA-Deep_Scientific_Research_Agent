# DSRA V2 — Architecture & Technology Decisions

> **Living Document** — Every significant decision logged here with rationale.
> Last updated: 2026-07-01

---

## Decision Log

### ADR-001: Backend Framework — FastAPI

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** Need an async-capable Python web framework for the API layer.

**Decision:** FastAPI

**Rationale:**
- Native async/await support — critical for parallel agent execution
- Automatic OpenAPI/Swagger documentation
- Pydantic v2 integration native
- Server-Sent Events (SSE) support for streaming
- Dependency injection system for clean architecture
- Industry adoption and long-term maintenance confidence

**Alternatives Considered:**
- Django REST Framework — synchronous-first, heavyweight for this use case
- Flask — no native async, no automatic docs
- Litestar — newer, less ecosystem maturity

**Future Impact:** SSE streaming and async agent orchestration depend on this choice.

---

### ADR-002: Database — PostgreSQL + SQLAlchemy 2.0 (async) + Alembic

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** Need a persistent, queryable store for research sessions, sources, claims, and reports.

**Decision:** PostgreSQL as the database engine, SQLAlchemy 2.0 with async engine, Alembic for migrations.

**Rationale:**
- PostgreSQL JSONB allows flexible storage for variable report schemas
- SQLAlchemy 2.0 async ORM eliminates the blocking I/O problem of V1
- Alembic gives us schema versioning and migration history
- PostgreSQL full-text search reduces need for external search service in early phases
- Industry standard combination — every Python senior engineer knows it

**Alternatives Considered:**
- MongoDB — document-native but loses relational integrity for claim-source relationships
- SQLite — not suitable for production concurrent access
- Raw asyncpg — too low-level, loses ORM benefits

**Future Impact:** All agents interact with DB through repository pattern — never directly.

---

### ADR-003: Vector Database — ChromaDB

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** Need semantic search over past research, source content, and evidence chunks.

**Decision:** ChromaDB as the primary vector store.

**Rationale:**
- Local-first — no external service dependency in development
- Python-native client
- Supports multiple embedding backends
- Can be upgraded to cloud-hosted Chroma or swapped to Pinecone/Weaviate without changing the abstraction layer
- FAISS is an alternative but has no built-in metadata filtering

**Alternatives Considered:**
- FAISS — fast but no metadata filtering, no persistence management
- Pinecone — cloud-only, adds cost and external dependency
- Weaviate — more complex setup for local development
- Qdrant — strong candidate for Phase 2 upgrade if scale requires it

**Future Impact:** All memory operations go through a `VectorStore` abstraction — ChromaDB is the default implementation.

---

### ADR-004: LLM Access — Abstracted LLMGateway

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** Need to call LLMs from multiple agents without tight coupling to any provider.

**Decision:** Create an `LLMGateway` abstraction layer. OpenAI async SDK is the primary implementation. Agents NEVER import OpenAI directly.

**Rationale:**
- Allows model swapping (GPT-4o → Claude → Gemini) without touching agent code
- Centralizes retry logic, exponential backoff, and rate limiting
- Enables cost tracking and token logging in one place
- Allows mock LLM responses in tests
- Enables fallback routing (primary model fails → fallback model)

**Alternatives Considered:**
- LangChain — adds abstraction layer but too much magic; hides what's happening
- LiteLLM — good candidate for the gateway implementation layer internally

**Future Impact:** Every agent receives an `LLMGateway` instance via dependency injection.

---

### ADR-005: HTTP Client for Source Fetching — aiohttp

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** V1 used synchronous `requests` library — a critical flaw in an async environment.

**Decision:** `aiohttp` for all outbound HTTP calls from retriever agents.

**Rationale:**
- Native async — non-blocking, compatible with FastAPI event loop
- Session reuse with `aiohttp.ClientSession` reduces connection overhead
- Built-in timeout and retry capability
- `httpx` is a strong alternative with requests-compatible API

**Alternatives Considered:**
- `httpx` — also async-capable, cleaner API; may use in future
- `requests` — synchronous, unacceptable in async context

---

### ADR-006: Validation — Pydantic v2

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** Need strict typed validation for all agent inputs, outputs, API requests, and database models.

**Decision:** Pydantic v2 throughout the entire codebase.

**Rationale:**
- Native FastAPI integration
- Pydantic v2 is significantly faster than v1 (Rust core)
- `model_config` provides strict mode (no coercion)
- Generates JSON Schema automatically
- SQLAlchemy-Pydantic bridge available

---

### ADR-007: Structured Logging — structlog

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** V1 used bare `print()` statements. No observability, no log aggregation possible.

**Decision:** `structlog` as the logging library.

**Rationale:**
- JSON-formatted output — compatible with log aggregators (Datadog, Loki, CloudWatch)
- Context binding — attach request ID, session ID, agent name to all log lines
- Async-safe processors
- No performance overhead from standard library's slow string formatting

---

### ADR-008: Frontend — React + Vite + TypeScript

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** V1 had a non-functional 1,587-byte Jinja2 template. V2 needs a professional research platform UI.

**Decision:** React with Vite bundler and TypeScript.

**Rationale:**
- Vite provides fast HMR for development
- React component model suits the complex agent timeline UI
- TypeScript ensures API contract safety between frontend and backend
- SSE client support is native in browser `EventSource` API
- Large ecosystem for data visualization (evidence confidence charts)

**Alternatives Considered:**
- Next.js — adds SSR complexity not needed for a dashboard-heavy internal tool
- Vue.js — smaller ecosystem, less developer availability
- Svelte — excellent but smaller hiring pool for maintenance

---

### ADR-009: Streaming — Server-Sent Events (SSE)

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** Users need real-time visibility into agent execution without a 60-second blank screen.

**Decision:** Server-Sent Events via FastAPI `StreamingResponse`.

**Rationale:**
- Simpler than WebSockets for one-directional server-to-client streaming
- Native browser `EventSource` API — no client library needed
- Reconnects automatically on connection drops
- Works through HTTP/1.1 and HTTP/2
- Sufficient for the research progress use case (no bidirectional needed during execution)

**Alternatives Considered:**
- WebSockets — bidirectional not needed; adds complexity
- Long polling — inefficient, higher latency

---

### ADR-010: Agent Architecture — BaseAgent Abstract Class

**Status:** ACCEPTED
**Date:** 2026-07-01

**Context:** V1 had no agent contracts. Every class was a grab bag of methods with no enforced interface.

**Decision:** Every agent implements a `BaseAgent` ABC with enforced `execute()` method, typed `InputSchema`, `OutputSchema`, `system_prompt`, retry logic, and structured logging.

**Rationale:**
- Enforces Single Responsibility Principle
- Makes every agent independently testable with mock I/O
- Allows the Orchestrator to call any agent through a uniform interface
- Metric collection can be added once in `BaseAgent` and inherited

---

*Document maintained by: Lead Architecture Review*
*Last updated: 2026-07-01*
