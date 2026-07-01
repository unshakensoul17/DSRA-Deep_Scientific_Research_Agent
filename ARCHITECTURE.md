# DSRA V2 — Architecture Document

> **Living Document** — Updated after every significant change.
> Last updated: 2026-07-01 | Phase: 2

---

## 1. System Overview

DSRA V2 is a **multi-agent AI research platform**. It orchestrates a directed acyclic graph (DAG) of specialized agents to perform deep, iterative, evidence-grounded research on any topic.

It is **not** a chatbot. It is **not** an LLM wrapper. It is a research engine.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT (Browser)                           │
│  React + Vite + TypeScript                                          │
│  SSE EventSource  |  REST API calls  |  Dark/Light mode            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────────────┐
│                     API LAYER — FastAPI /api/v1/                    │
│  Auth Middleware  |  Rate Limiting  |  Input Validation             │
│  SSE StreamingResponse  |  OpenAPI Docs                             │
└──────────┬──────────────────────────────────────┬───────────────────┘
           │                                      │
┌──────────▼──────────┐               ┌───────────▼───────────────────┐
│   ORCHESTRATOR      │               │   REPOSITORY LAYER            │
│   State Machine     │◄──────────────►  (Only layer touching DB)     │
│   DAG Workflow      │               │  Sessions, Sources, Claims    │
│   SSE Event Bus     │               │  Reports, AgentLogs           │
└──────────┬──────────┘               └───────────┬───────────────────┘
           │                                      │
    ┌──────┴──────────────────────────┐  ┌────────▼────────┐
    │         AGENT LAYER             │  │   PostgreSQL    │
    │                                 │  │   (Primary DB)  │
    │  PlannerAgent                   │  └─────────────────┘
    │  ResearchAgent (per source)     │
    │  EvidenceAgent                  │  ┌─────────────────┐
    │  VerificationAgent              │  │   ChromaDB      │
    │  GapAnalysisAgent               │  │   (Vector DB)   │
    │  CriticAgent                    │  └─────────────────┘
    │  WriterAgent                    │
    │  VisualizationAgent             │
    │  ExportAgent                    │
    └──────────┬──────────────────────┘
               │
    ┌──────────▼──────────────────────┐
    │         INFRASTRUCTURE          │
    │                                 │
    │  LLMGateway (OpenAI async)      │
    │  RetrieverAdapters (aiohttp)    │
    │  MemoryEngine (ChromaDB)        │
    │  ResearchCache (Redis/in-mem)   │
    └─────────────────────────────────┘
```

---

## 3. Module Structure

```
dsra-v2/
│
├── backend/                          # Python backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory
│   │   │
│   │   ├── api/                      # API layer
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── routers/
│   │   │           ├── auth.py       # POST /auth/register, /auth/login
│   │   │           ├── research.py   # POST/GET /research/sessions, SSE stream
│   │   │           ├── reports.py    # GET /reports/{id}, export
│   │   │           └── health.py     # GET /health
│   │   │
│   │   ├── agents/                   # Agent layer (pure functions, typed I/O)
│   │   │   ├── base.py               # BaseAgent ABC
│   │   │   ├── planner.py            # PlannerAgent
│   │   │   ├── researcher.py         # ResearchAgent (source-type agnostic)
│   │   │   ├── evidence.py           # EvidenceAgent
│   │   │   ├── verification.py       # VerificationAgent
│   │   │   ├── gap_analysis.py       # GapAnalysisAgent
│   │   │   ├── critic.py             # CriticAgent
│   │   │   ├── writer.py             # WriterAgent
│   │   │   ├── visualization.py      # VisualizationAgent
│   │   │   └── export.py             # ExportAgent
│   │   │
│   │   ├── core/                     # Orchestration engine
│   │   │   ├── orchestrator.py       # Main Orchestrator class
│   │   │   ├── workflow.py           # DAG WorkflowEngine
│   │   │   ├── state.py              # ResearchSession state machine
│   │   │   └── events.py             # SSE event type definitions
│   │   │
│   │   ├── retrievers/               # Source adapter layer
│   │   │   ├── base.py               # BaseRetriever Protocol
│   │   │   ├── arxiv.py              # feedparser-based arXiv adapter
│   │   │   ├── semantic_scholar.py   # Async Semantic Scholar adapter
│   │   │   ├── wikipedia.py          # Async Wikipedia adapter
│   │   │   ├── google_cse.py         # Async Google CSE adapter
│   │   │   └── pubmed.py             # Async PubMed adapter
│   │   │
│   │   ├── llm/                      # LLM abstraction layer
│   │   │   ├── gateway.py            # LLMGateway (retry, fallback, cost tracking)
│   │   │   ├── providers/
│   │   │   │   ├── openai.py         # OpenAI async provider
│   │   │   │   └── fallback.py       # Fallback chain provider
│   │   │   └── prompts/              # Versioned, typed prompt templates
│   │   │       ├── base.py           # BasePrompt
│   │   │       ├── planner.py
│   │   │       ├── evidence.py
│   │   │       ├── verification.py
│   │   │       ├── gap_analysis.py
│   │   │       ├── critic.py
│   │   │       └── writer.py
│   │   │
│   │   ├── memory/                   # Memory layer
│   │   │   ├── short_term.py         # In-session evidence context
│   │   │   ├── long_term.py          # ChromaDB vector store wrapper
│   │   │   ├── cache.py              # Research result cache (TTL-based)
│   │   │   └── knowledge_graph.py    # Entity relationship tracker
│   │   │
│   │   ├── db/                       # Database layer
│   │   │   ├── base.py               # SQLAlchemy declarative base
│   │   │   ├── session.py            # Async session factory
│   │   │   ├── models/               # ORM models
│   │   │   │   ├── user.py
│   │   │   │   ├── research_session.py
│   │   │   │   ├── source.py
│   │   │   │   ├── claim.py
│   │   │   │   ├── report.py
│   │   │   │   └── agent_log.py
│   │   │   └── repositories/         # Repository pattern (query logic)
│   │   │       ├── base.py
│   │   │       ├── research_session.py
│   │   │       ├── source.py
│   │   │       ├── claim.py
│   │   │       └── report.py
│   │   │
│   │   ├── schemas/                  # Pydantic I/O contracts
│   │   │   ├── agents/               # Agent input/output schemas
│   │   │   │   ├── planner.py
│   │   │   │   ├── researcher.py
│   │   │   │   ├── evidence.py
│   │   │   │   ├── verification.py
│   │   │   │   ├── gap_analysis.py
│   │   │   │   ├── critic.py
│   │   │   │   ├── writer.py
│   │   │   │   └── export.py
│   │   │   ├── api/                  # API request/response schemas
│   │   │   │   ├── auth.py
│   │   │   │   ├── research.py
│   │   │   │   └── reports.py
│   │   │   └── common.py             # Shared types (SourceResult, Claim, etc.)
│   │   │
│   │   ├── config/
│   │   │   └── settings.py           # Pydantic BaseSettings
│   │   │
│   │   ├── middleware/
│   │   │   ├── auth.py               # JWT validation
│   │   │   └── rate_limit.py         # SlowAPI rate limiting
│   │   │
│   │   └── exceptions/
│   │       ├── base.py               # Custom exception hierarchy
│   │       └── handlers.py           # FastAPI exception handlers
│   │
│   ├── migrations/                   # Alembic migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── agents/               # Per-agent unit tests
│   │   │   ├── retrievers/           # Per-retriever unit tests
│   │   │   └── core/                 # Orchestrator/state machine tests
│   │   ├── integration/              # End-to-end API tests
│   │   └── conftest.py               # Fixtures (mock LLM, mock DB, etc.)
│   │
│   ├── alembic.ini
│   ├── pyproject.toml                # Dependencies + tooling config
│   └── .env.example
│
├── frontend/                         # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── sidebar/              # History, Collections, Templates
│   │   │   ├── workspace/            # Input, Options, Progress Timeline
│   │   │   ├── evidence/             # Evidence + Citation viewer
│   │   │   ├── report/               # Report viewer + streaming output
│   │   │   └── common/               # Button, Card, Badge, Spinner, etc.
│   │   ├── pages/
│   │   │   ├── ResearchPage.tsx
│   │   │   ├── ReportPage.tsx
│   │   │   └── HistoryPage.tsx
│   │   ├── hooks/
│   │   │   ├── useSSE.ts             # Server-Sent Events hook
│   │   │   ├── useResearch.ts        # Research session management
│   │   │   └── useReport.ts          # Report data hook
│   │   ├── services/
│   │   │   ├── api.ts                # Typed API client
│   │   │   └── sse.ts                # SSE client wrapper
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript type definitions
│   │   └── styles/
│   │       └── index.css             # Design system variables
│   ├── package.json
│   └── vite.config.ts
│
├── docs/
│   ├── PHASE_1_ANALYSIS.md
│   └── PHASE_2_ARCHITECTURE.md       # This document
│
├── scripts/
│   ├── dev.sh                        # Start backend + frontend dev servers
│   └── migrate.sh                    # Run Alembic migrations
│
├── PROJECT_STATE.md
├── ARCHITECTURE.md                   # → Points here
├── AGENTS.md
├── API_SPEC.md
├── DECISIONS.md
└── TODO.md
```

---

## 4. Orchestrator State Machine

The `ResearchSession` progresses through a strict state machine. No agent can be called outside its designated state. The Orchestrator enforces all transitions.

```
                        ┌─────────┐
                        │ CREATED │
                        └────┬────┘
                             │ start_research()
                        ┌────▼────┐
                        │PLANNING │  ← PlannerAgent
                        └────┬────┘
                             │ plan_complete
                        ┌────▼──────┐
                    ┌──►│ RETRIEVAL │  ← ResearchAgents (parallel per source)
                    │   └────┬──────┘
                    │        │ sources_fetched
                    │   ┌────▼─────────────┐
                    │   │EVIDENCE_EXTRACTION│  ← EvidenceAgent
                    │   └────┬─────────────┘
                    │        │ evidence_extracted
                    │   ┌────▼────────┐
                    │   │VERIFICATION │  ← VerificationAgent
                    │   └────┬────────┘
                    │        │ verification_complete
                    │   ┌────▼──────────┐
                    │   │ GAP_ANALYSIS  │  ← GapAnalysisAgent
                    │   └────┬──────────┘
                    │        │
                    │   ┌────▼──────────────────────────────┐
                    │   │  gaps_found AND iter < max_iter?   │
                    │   └────┬──────────────┬───────────────┘
                    │        │ YES           │ NO
                    │   ┌────▼────────┐ ┌───▼────┐
                    └───┤  ITERATING  │ │WRITING │ ← WriterAgent
                        └─────────────┘ └───┬────┘
                                            │ draft_complete
                                        ┌───▼──────┐
                                    ┌──►│ CRITIQUE │ ← CriticAgent
                                    │   └───┬──────┘
                                    │       │
                                    │  ┌────▼──────────────────────────────┐
                                    │  │ critique_failed AND rev < max_rev? │
                                    │  └────┬─────────────┬────────────────┘
                                    │       │ YES          │ NO
                                    └───────┘         ┌────▼─────────────┐
                                                      │  VISUALIZATION   │ ← VisualizationAgent
                                                      └────┬─────────────┘
                                                           │ viz_complete
                                                      ┌────▼──────┐
                                                      │  EXPORT   │ ← ExportAgent
                                                      └────┬──────┘
                                                           │ export_complete
                                                      ┌────▼──────────┐
                                                      │   COMPLETED   │
                                                      └───────────────┘

          ANY STATE ──► FAILED     (on unrecoverable error)
          ANY STATE ──► CANCELLED  (on user cancel)
```

**State Transition Rules:**
- Transitions are atomic — the Orchestrator updates DB state before executing the next agent
- Every state transition emits an SSE event to the client
- Failed transitions trigger retry logic before transitioning to `FAILED`
- `ITERATING` re-enters `RETRIEVAL` with new queries from `GapAnalysisAgent`
- Max iterations is configurable per session (default: 3)
- Max critique revisions is configurable (default: 2)

---

## 5. Agent Data Flow

```
User Input (topic, depth, options)
        │
        ▼
┌───────────────────┐
│   PlannerAgent    │
│                   │
│  IN:  ResearchGoal│
│  OUT: ResearchPlan│
│       (queries,   │
│        sources,   │
│        complexity)│
└────────┬──────────┘
         │ ResearchPlan
         ▼
┌────────────────────────────────────────────────────┐
│           ResearchAgent × N  (parallel)            │
│                                                    │
│  IN:  SearchQuery (one per source type)            │
│  OUT: List[SourceResult]                           │
│                                                    │
│  ArxivRetriever  |  SemanticScholarRetriever       │
│  WikipediaRetriever  |  GoogleCSERetriever         │
│  PubMedRetriever                                   │
└────────────────────────────────┬───────────────────┘
                                 │ List[SourceResult] (merged, deduplicated, ranked)
                                 ▼
                     ┌───────────────────────┐
                     │    EvidenceAgent      │
                     │                       │
                     │  IN:  List[SourceResult]│
                     │  OUT: List[EvidencePiece]│
                     │       (claim, source,  │
                     │        relevance_score,│
                     │        excerpt)        │
                     └──────────┬────────────┘
                                │ List[EvidencePiece]
                                ▼
                     ┌───────────────────────┐
                     │  VerificationAgent    │
                     │                       │
                     │  IN:  List[Evidence]  │
                     │  OUT: List[Verified   │
                     │       Claim] with     │
                     │       confidence score│
                     │       & contradiction │
                     │       flags           │
                     └──────────┬────────────┘
                                │ List[VerifiedClaim]
                                ▼
                     ┌───────────────────────┐
                     │   GapAnalysisAgent    │
                     │                       │
                     │  IN:  Claims + Plan   │
                     │  OUT: GapReport       │
                     │       (gaps, new      │
                     │        queries,       │
                     │        iterate?)      │
                     └──────────┬────────────┘
                                │
                   ┌────────────▼────────────┐
                   │      WriterAgent        │
                   │                         │
                   │  IN:  VerifiedClaims +  │
                   │       Sources + Plan    │
                   │  OUT: ReportDraft       │
                   │       (all sections)    │
                   └────────────┬────────────┘
                                │ ReportDraft
                                ▼
                   ┌────────────────────────┐
                   │      CriticAgent       │
                   │                        │
                   │  IN:  ReportDraft      │
                   │  OUT: CritiqueResult   │
                   │       (scores,         │
                   │        weaknesses,     │
                   │        approved?)      │
                   └────────────┬───────────┘
                                │ Approved ReportDraft
                                ▼
                   ┌────────────────────────┐
                   │  VisualizationAgent    │
                   │                        │
                   │  IN:  FinalReport      │
                   │  OUT: VisualizationBundle│
                   │       (tables, charts) │
                   └────────────┬───────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │      ExportAgent       │
                   │                        │
                   │  IN:  Report + Viz     │
                   │  OUT: ExportBundle     │
                   │       (PDF, MD,        │
                   │        HTML, JSON)     │
                   └────────────────────────┘
```

---

## 6. Database Schema (Preview)

```sql
-- Users
users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       VARCHAR(255) UNIQUE NOT NULL,
  hashed_pw   VARCHAR(255),
  api_key     VARCHAR(64) UNIQUE,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
)

-- Research Sessions (core entity)
research_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  topic           TEXT NOT NULL,
  state           VARCHAR(32) NOT NULL DEFAULT 'CREATED',
  depth           SMALLINT DEFAULT 2,          -- 1=shallow, 2=normal, 3=deep
  iteration_count SMALLINT DEFAULT 0,
  max_iterations  SMALLINT DEFAULT 3,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  completed_at    TIMESTAMPTZ
)

-- Individual search queries generated by PlannerAgent
research_queries (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
  query_text  TEXT NOT NULL,
  source_type VARCHAR(32) NOT NULL,   -- arxiv|semantic_scholar|google|wikipedia|pubmed
  iteration   SMALLINT DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
)

-- Retrieved source documents
sources (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
  query_id        UUID REFERENCES research_queries(id) ON DELETE SET NULL,
  title           TEXT NOT NULL,
  url             TEXT,
  snippet         TEXT,
  full_content    TEXT,               -- Retrieved full text (where possible)
  source_type     VARCHAR(32) NOT NULL,
  quality_score   FLOAT,              -- 0.0–1.0 assigned by EvidenceAgent
  authors         JSONB,              -- JSON array of author names
  year            SMALLINT,
  doi             VARCHAR(128),
  fetched_at      TIMESTAMPTZ DEFAULT NOW()
)

-- Extracted evidence pieces (claim-source mappings)
claims (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
  text            TEXT NOT NULL,
  confidence      FLOAT NOT NULL,     -- 0.0–1.0
  status          VARCHAR(16) NOT NULL DEFAULT 'UNVERIFIED',
                  -- UNVERIFIED | VERIFIED | CONTRADICTED | INSUFFICIENT_EVIDENCE
  source_ids      UUID[],             -- PostgreSQL array of source UUIDs
  iteration       SMALLINT DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
)

-- Detailed verification results per claim
verification_results (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  claim_id                UUID REFERENCES claims(id) ON DELETE CASCADE,
  supporting_source_ids   UUID[],
  contradicting_source_ids UUID[],
  confidence              FLOAT NOT NULL,
  reasoning               TEXT,       -- LLM-generated reasoning for the verdict
  verified_at             TIMESTAMPTZ DEFAULT NOW()
)

-- Final research reports
reports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
  title           TEXT NOT NULL,
  executive_summary TEXT,
  sections        JSONB NOT NULL DEFAULT '{}',
  key_findings    TEXT[] DEFAULT '{}',
  methodology     TEXT,
  limitations     TEXT,
  conclusion      TEXT,
  references      JSONB DEFAULT '[]',
  status          VARCHAR(16) DEFAULT 'DRAFT',  -- DRAFT | FINAL
  critique_score  FLOAT,
  export_paths    JSONB DEFAULT '{}',   -- {pdf: path, md: path, html: path}
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  finalized_at    TIMESTAMPTZ
)

-- Per-agent execution audit log
agent_execution_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
  agent_name      VARCHAR(64) NOT NULL,
  state_entered   VARCHAR(32) NOT NULL,
  input_tokens    INTEGER,
  output_tokens   INTEGER,
  duration_ms     INTEGER,
  retry_count     SMALLINT DEFAULT 0,
  error_message   TEXT,
  metadata        JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT NOW()
)
```

---

## 7. SSE Event Schema

Every state transition emits a typed SSE event to the connected client:

```
event: session_state_changed
data: {"session_id": "...", "state": "PLANNING", "timestamp": "..."}

event: agent_started
data: {"agent": "PlannerAgent", "session_id": "...", "timestamp": "..."}

event: agent_completed
data: {"agent": "PlannerAgent", "duration_ms": 1200, "output_preview": "..."}

event: source_fetched
data: {"source_type": "arxiv", "count": 6, "session_id": "..."}

event: claim_verified
data: {"claim_id": "...", "status": "VERIFIED", "confidence": 0.87}

event: gap_detected
data: {"gaps": ["missing mechanism details", "no clinical trials data"], "iteration": 1}

event: report_section_complete
data: {"section": "Background", "word_count": 450}

event: research_complete
data: {"session_id": "...", "report_id": "...", "duration_ms": 45000}

event: error
data: {"agent": "VerificationAgent", "error": "Rate limit exceeded", "retry_in_ms": 5000}
```

---

## 8. Security Architecture

```
Request → CORS middleware
       → Auth middleware (JWT decode → user_id)
       → Rate limit middleware (by user_id + IP)
       → Input validation (Pydantic)
       → Router handler
       → Repository (parameterized queries only)
       → Response (output model serialization)
```

**Secrets:** All credentials in environment variables via Pydantic `BaseSettings`. Never in code.
**SQL Injection:** Prevented by SQLAlchemy ORM parameterization.
**Prompt Injection:** Topic input sanitized and length-capped before inclusion in prompts.
**File traversal:** Export paths generated internally, never from user input.

---

## 9. Performance Architecture

| Bottleneck | Solution |
|-----------|---------|
| Source fetching (4–12s serial) | `asyncio.gather()` parallel fetching |
| LLM calls (3–15s each) | Async OpenAI client, streaming where applicable |
| DB queries | SQLAlchemy async engine, proper indexes |
| Repeated queries | TTL-based research cache (in-memory, Phase 1 → Redis, Phase 2) |
| Frontend blocking | SSE streaming of partial results |

---

*Document maintained by: Lead Architecture Review*
*Last updated: 2026-07-01*
