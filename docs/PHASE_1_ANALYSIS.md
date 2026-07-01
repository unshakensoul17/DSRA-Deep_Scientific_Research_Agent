# DSRA V2 — PHASE 1: Legacy Analysis & Migration Document

> **Status:** COMPLETE
> **Author:** Lead Architecture Review
> **Date:** 2026-07-01
> **Purpose:** Full forensic audit of DSRA V1 prototype. Defines every weakness, design flaw, and missing capability. Forms the binding contract for what DSRA V2 must fix.

---

## 1. Executive Summary

The original DSRA prototype is a **thin LLM wrapper** disguised as a research platform. It performs:

1. Fetches snippets from 4 sources (Google, Wikipedia, arXiv, Semantic Scholar)
2. Concatenates those snippets into a single prompt string
3. Asks GPT-4o-mini to write a research report
4. Saves output as JSON + Markdown + PDF

**This is not a research system.** It is an automated summarization pipeline with a broken orchestrator, no real agents, no verification, no state management, no memory, no iterative refinement, and no quality guarantees.

---

## 2. Critical Architecture Failures

### 2.1 — There Are No Agents

**Finding:** The system calls itself "multi-agent" but contains zero agents in any meaningful definition. The `Retriever`, `Synthesizer`, and `ReflectionAgent` classes are simple Python classes with no:
- Input schema validation
- Output schema validation
- System prompt isolation
- Retry logic, Logging, Metrics, Error boundaries, State awareness

**Impact:** The entire premise of the system is false. Every module does too much or too little with no well-defined contracts.

**V2 Fix:** Every agent implements a `BaseAgent` abstract class with enforced input/output schemas, system prompts, retry logic, logging, and metrics.

---

### 2.2 — The Orchestrator Does Not Exist

**Finding:** `main.py` is the de facto orchestrator. It calls `Retriever` → `Synthesizer` **sequentially** and has **dead code after `if __name__ == "__main__":`** that runs on every import:

```python
# main.py — CRITICAL BUG
if __name__ == "__main__":
    main()

# These 12 lines execute on EVERY IMPORT — broken
from core.dashboard import DashboardGenerator
dash = DashboardGenerator()
dash.build_dashboard()
```

No state machine, no workflow tracking, no timeout handling, no retry orchestration, cannot resume failed research.

**Impact:** The system cannot be safely imported. The "orchestrator" fails immediately under concurrent load.

**V2 Fix:** Dedicated async `Orchestrator` with proper state machine, DAG task queue, and workflow graph.

---

### 2.3 — Synchronous, Sequential, Blocking Pipeline

**Finding:** All source fetching done **sequentially** with synchronous `requests.get()` calls:

```python
results += self._fetch_from_google(query)           # blocks
results += self._fetch_from_wikipedia(query)         # blocks
results += self._fetch_from_arxiv(query)             # blocks
results += self._fetch_from_semantic_scholar(query)  # blocks
```

Total time = sum of 4 network calls = 4–12 seconds pure blocking I/O in FastAPI's async event loop.

**Impact:** Fundamentally unscalable. Blocks all concurrent users. Starves the event loop.

**V2 Fix:** `asyncio` + `aiohttp` parallel fetching. All independent agents run concurrently.

---

### 2.4 — Infinite Retry Loop (Critical Production Bug)

**Finding:** `synthesizer.py` contains an unbounded `while True:` loop with no max iterations or timeout:

```python
while True:
    try:
        data = json.loads(raw)
        if incomplete(data["summary"]):
            time.sleep(1.5)      # BLOCKS the event loop
            raw = generate()
            continue
        break
    except:
        time.sleep(1.5)
        raw = generate()
        # NO EXIT CONDITION ON PERSISTENT FAILURE
```

**Impact:** If the LLM consistently returns malformed JSON (rate limit, model degradation, context overflow), this loops **forever**, freezing the entire server process.

**V2 Fix:** Configurable max retry count, exponential backoff, circuit breaker pattern, fallback model routing.

---

### 2.5 — No Verification, No Evidence, No Confidence Scores

**Finding:** The synthesizer asks the LLM to produce a report using raw text snippets. The cited sources in the output are **LLM-generated hallucinations** — not validated references. Nothing in the system:
- Checks if cited URLs exist
- Cross-references claims across multiple sources
- Assigns confidence scores to any claim
- Detects contradictions between sources

**Impact:** The system produces plausible-looking but unverified research. Hallucinated citations presented as fact — dangerous in academic or professional contexts.

**V2 Fix:** `VerificationAgent` independently cross-checks every claim. Confidence scores. Source URL validation. Claim-source mapping persisted in the database.

---

### 2.6 — Broken Memory System

**Finding:** `MemoryEngine` stores a flat JSON file with three arrays — `topics` (strings), `key_facts` (strings), `cross_links` (naive "TopicA ↔ TopicB" strings). This provides:
- No semantic search
- No vector embeddings
- No contextual retrieval
- **Is never read back into any agent's context — completely unused**

**Impact:** Every research session starts from absolute zero. "Memory" is a marketing term on a text file.

**V2 Fix:** ChromaDB for vector storage, semantic chunking, embedding-based retrieval, knowledge graph for entity relationships.

---

### 2.7 — No Database. State Lives in the Filesystem.

**Finding:** All state is loose JSON/PDF files in `data/outputs/`. Dashboard reads them via `os.listdir()` glob scan. There is no database schema, query capability, transaction safety, or user ownership of research.

**Impact:** Cannot scale past one server. Files can be lost, corrupted, or race under concurrent writes. No audit trail.

**V2 Fix:** PostgreSQL + Alembic. Models: `User`, `ResearchSession`, `Source`, `Claim`, `VerificationResult`, `AgentExecutionLog`, `Report`.

---

### 2.8 — The Reflection Agent is a Wrapper Around Another LLM Call

**Finding:** `critique_report()` dumps the entire report JSON into GPT-4o-mini and asks it to critique itself. `regenerate_improved()` dumps the critique back and asks for a rewrite — 3x LLM calls, ungrounded, linear (not iterative), and the improved report is **never used** by anything.

**V2 Fix:** Structured `CriticAgent` with specific evaluation rubrics. Gap analysis feeds back into the retrieval loop. Iterative convergence with a defined quality threshold.

---

### 2.9 — arXiv Parsing is Brittle String Splitting

**Finding:** arXiv XML parsed with string splits — not an XML parser. Breaks on nested elements, CDATA, encoding changes, or API format updates. All failures silently caught and return `[]`.

**V2 Fix:** `feedparser` library. Pydantic models for structured validation.

---

### 2.10 — Bare `except:` Clauses Throughout

**Finding:** Multiple modules use bare `except:` or `except Exception` followed by `print()` or `return []`, silently swallowing all errors. Debugging, monitoring, and alerting are all impossible.

**V2 Fix:** `structlog` structured logging. Specific exception types. Error rate metrics.

---

### 2.11 — No Input Validation

**Finding:** Research topics accepted as raw strings — no length limits, no sanitization, no injection protection, no rate limiting.

**V2 Fix:** Pydantic validators, input length limits, content filtering, rate limiting middleware.

---

### 2.12 — No Authentication. No Multi-Tenancy.

**Finding:** Zero authentication on the FastAPI server. Any caller triggers expensive LLM + API calls. No users, no sessions, no ownership.

**V2 Fix:** JWT-based authentication (extensible to OAuth2). User-scoped research sessions. API key management.

---

### 2.13 — No Streaming. No Progress Visibility.

**Finding:** `/run` endpoint blocks the HTTP connection for 15–60 seconds then returns the full response. No progress updates, no streaming, no partial results, no cancellation.

**Impact:** User sees a blank page for up to 60 seconds. Completely unacceptable UX.

**V2 Fix:** Server-Sent Events (SSE) for real-time agent progress. Token streaming from LLM. Per-phase status events.

---

### 2.14 — Prompt Engineering is Naive and Fragile

**Finding:** Single monolithic prompt — one shot, no system role separation, no chain-of-thought, no few-shot examples, no version control, hardcoded inside the class method.

**V2 Fix:** Separate system prompts per agent. Chain-of-thought reasoning. Prompt versioning. Template-based prompts with variable injection.

---

### 2.15 — Frontend is Unusable for a Research Platform

**Finding:** 1,587-byte Jinja2 template + 1,465-byte CSS. No loading states, no agent activity, no dark mode, no streaming progress, no research history, no evidence viewer, no citation viewer.

**V2 Fix:** React + Vite + TypeScript. Real-time agent activity timeline. Evidence + citation viewer with confidence scores. Dark/light mode. Research history.

---

## 3. Full Weakness Inventory

| ID | Category | Severity | Finding |
|----|----------|----------|---------|
| W-01 | Architecture | CRITICAL | No real agents — plain classes with no typed contracts |
| W-02 | Architecture | CRITICAL | Dead code executes on import in main.py |
| W-03 | Performance | CRITICAL | Synchronous blocking I/O inside FastAPI async server |
| W-04 | Reliability | CRITICAL | Infinite retry loop — no circuit breaker or timeout |
| W-05 | Quality | CRITICAL | LLM-hallucinated citations — zero verification |
| W-06 | Research | CRITICAL | No gap detection — research ends after one pass |
| W-07 | Research | CRITICAL | No source quality ranking — all sources treated equally |
| W-08 | Data | HIGH | No database — state in loose filesystem files |
| W-09 | Intelligence | HIGH | Memory system is a non-functional text file |
| W-10 | Quality | HIGH | Reflection agent adds 3x cost with zero measurable quality |
| W-11 | Reliability | HIGH | arXiv XML parsed with brittle string splitting |
| W-12 | Reliability | HIGH | Bare except clauses swallow all errors silently |
| W-13 | Security | HIGH | Zero input validation |
| W-14 | Security | HIGH | No authentication / no multi-tenancy |
| W-15 | UX | HIGH | No streaming — 60-second blank UI |
| W-16 | Testing | HIGH | Zero tests of any kind |
| W-17 | Observability | HIGH | No structured logging, no metrics, no tracing |
| W-18 | Scalability | HIGH | Single-threaded — cannot serve concurrent users |
| W-19 | Research | HIGH | Only snippets fetched — full source content never retrieved |
| W-20 | Research | HIGH | Deduplication only by naive title+link string match |
| W-21 | Quality | MEDIUM | Single-pass monolithic prompt — no chain-of-thought |
| W-22 | UX | MEDIUM | Frontend non-functional for professional research use |
| W-23 | Config | MEDIUM | Hardcoded relative paths (data/outputs) |
| W-24 | Config | LOW | Empty .env.example — zero variable documentation |
| W-25 | Output | MEDIUM | Fixed 4-section report schema — not extensible |

---

## 4. What Is Worth Keeping (Concepts Only)

Nothing from V1 is directly reusable in production form. These **concepts** are preserved and reimplemented correctly in V2:

| Concept | V1 Implementation | V2 Approach |
|---------|-------------------|-------------|
| Multi-source retrieval | Sequential, sync, dicts | Async parallel, `BaseRetriever` adapters, Pydantic models |
| arXiv integration | String splitting | `feedparser` + Pydantic |
| Semantic Scholar | Basic REST call | Async client with retry, caching |
| PDF export | ReportLab basic | ReportLab with proper layout engine |
| Reflection/Critique | Single LLM call | Structured `CriticAgent` with rubrics |
| Dashboard | JSON file glob scan | Database query with aggregation |

---

## 5. V2 Architecture Requirements (Derived From This Analysis)

### 5.1 Agent Layer
- Abstract `BaseAgent` with enforced typed interface
- Single responsibility per agent; typed I/O, retry logic, structured logging, metrics
- Agents: `PlannerAgent`, `ResearchAgent`, `EvidenceAgent`, `VerificationAgent`, `GapAnalysisAgent`, `CriticAgent`, `WriterAgent`, `VisualizationAgent`, `ExportAgent`

### 5.2 Orchestration Layer
- Async `Orchestrator` with DAG-based workflow execution
- Parallel agent execution where dependencies allow
- Timeout, cancellation, and resume support
- Per-session state isolation

### 5.3 Retrieval Layer
- Async source adapters implementing `BaseRetriever` protocol
- Full content retrieval (not just snippets)
- Source quality scoring
- Rate limiting and result caching per source
- Sources: Google CSE, arXiv, Semantic Scholar, Wikipedia, PubMed

### 5.4 Verification Layer
- Claim extraction from synthesized text
- Source-claim mapping with per-claim confidence scores
- Cross-source contradiction detection
- URL validation and content fetching

### 5.5 Memory Layer
- Short-term: In-session ranked evidence context
- Long-term: ChromaDB with semantic search over past research
- Knowledge graph: Entity relationships across research sessions
- Research cache: Avoid re-fetching identical queries within TTL

### 5.6 Persistence Layer
- PostgreSQL with Alembic migrations
- SQLAlchemy 2.0 async ORM
- Models: `User`, `ResearchSession`, `ResearchQuery`, `Source`, `Claim`, `VerificationResult`, `AgentExecutionLog`, `Report`

### 5.7 API Layer
- FastAPI versioned router (`/api/v1/`)
- JWT authentication middleware
- SlowAPI rate limiting
- SSE streaming for real-time agent progress
- Full OpenAPI documentation

### 5.8 Frontend Layer
- React + Vite + TypeScript
- Real-time agent activity timeline (SSE client)
- Evidence + citation viewer with confidence scores
- Research history + saved reports
- Dark/light mode
- Streaming report generation

---

## 6. Technology Stack Decisions

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend framework | FastAPI | Async-native, typed, auto-docs, SSE support |
| ORM | SQLAlchemy 2.0 (async) | Type-safe, async-native, battle-tested |
| Migrations | Alembic | Industry standard for SQLAlchemy |
| Database | PostgreSQL | Reliability, JSONB for flexible fields |
| Vector DB | ChromaDB | Local-first, no external service dependency |
| LLM Client | OpenAI async SDK | Primary; abstracted via `LLMGateway` for model swapping |
| HTTP Client | aiohttp | Async HTTP for all source fetching |
| XML/Feed Parsing | feedparser | Industry standard for Atom/RSS (arXiv) |
| Validation | Pydantic v2 | Strict typed validation, fast, widely supported |
| Logging | structlog | Structured, JSON-compatible, async-safe |
| Testing | pytest + pytest-asyncio | Full async test support |
| Frontend | React + Vite + TypeScript | Fast dev server, component model, SSE client |
| Streaming | SSE via FastAPI `StreamingResponse` | Real-time progress without WebSocket complexity |
| Task Queue | asyncio.gather (Phase 1) → Celery/Redis (Phase 2) | Progressive complexity |

---

## 7. Migration Rules

1. **No code from V1 is copied directly.** All modules reimplemented from scratch.
2. **V1 output schema kept as reference** for backward compatibility with saved reports only.
3. **All source adapters produce a validated `SourceResult` Pydantic model** — never raw dicts.
4. **All LLM calls go through an `LLMGateway` abstraction** — never OpenAI SDK directly from an agent.
5. **All persistence goes through the repository layer** — agents never write files or DB rows directly.
6. **Every agent is independently unit-testable** with mock inputs/outputs.

---

## 8. Next Phase

**PHASE 2: Architecture Design**

- Full folder structure with module boundaries
- Complete data flow diagram
- Agent input/output Pydantic contracts
- Orchestrator state machine definition
- Database schema preview
- API route design preview

> **Awaiting approval to proceed to Phase 2.**

---

*Document maintained by: Lead Architecture Review*
*Last updated: 2026-07-01*
