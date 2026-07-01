# DSRA V2 — TODO Tracker

> **Living Document** — Updated after every phase.
> Last updated: 2026-07-01

---

## Phase 1 — Legacy Analysis ✅ COMPLETE

- [x] Clone and read all V1 source files
- [x] Document every architectural weakness (25 found)
- [x] Categorize weaknesses by severity (CRITICAL / HIGH / MEDIUM / LOW)
- [x] Identify what concepts are worth preserving
- [x] Define V2 architecture requirements from failures
- [x] Lock technology stack decisions
- [x] Define migration rules
- [x] Create PHASE_1_ANALYSIS.md
- [x] Create PROJECT_STATE.md
- [x] Create DECISIONS.md
- [x] Create TODO.md

---

## Phase 2 — Architecture Design ✅ COMPLETE

- [x] Define full folder/module structure for `dsra-v2/`
- [x] Define all module boundaries and responsibilities
- [x] Draw complete data flow diagram (User → Orchestrator → Agents → DB → Response)
- [x] Define Pydantic input/output schemas for every agent
- [x] Define Orchestrator state machine (states, transitions, events)
- [x] Preview database schema (tables and relationships)
- [x] Preview API route design (/api/v1/)
- [x] Create ARCHITECTURE.md
- [x] Create AGENTS.md (agent contracts)
- [x] Create API_SPEC.md (route preview)


---

## Phase 3 — Database Design ✅ COMPLETE

- [x] Finalize all database models with full field definitions
- [x] Define all foreign key relationships
- [x] Define indexes for query performance
- [x] Create Alembic migration setup
- [x] Create initial migration (baseline)
- [x] Write unit tests for all models

---

## Phase 4 — Orchestrator Design ✅ COMPLETE

- [x] Implement `ResearchSession` state machine
- [x] Implement `WorkflowEngine` with DAG execution
- [x] Implement parallel agent execution (asyncio.gather)
- [x] Implement timeout and cancellation
- [x] Implement SSE event emission from Orchestrator
- [x] Write unit tests for state transitions
- [x] Write integration tests for workflow execution


---

## Phase 5 — Planner Agent ✅ COMPLETE

- [x] Implement `BaseAgent` abstract class
- [x] Implement `LLMGateway` with retry and fallback
- [x] Implement `PlannerAgent` with typed I/O
- [x] Write system prompt for Planner
- [x] Implement task decomposition logic
- [x] Implement source selection logic
- [x] Write unit tests with mock LLM
- [x] Write integration tests


---

## Phase 6 — Retrieval Agents ⏳ NOT STARTED

- [ ] Implement `BaseRetriever` async protocol
- [ ] Implement `ArxivRetriever` (feedparser-based)
- [ ] Implement `SemanticScholarRetriever` (async)
- [ ] Implement `WikipediaRetriever` (async)
- [ ] Implement `GoogleCSERetriever` (async)
- [ ] Implement `PubMedRetriever` (async)
- [ ] Implement result deduplication (semantic, not string-match)
- [ ] Implement source quality scoring
- [ ] Implement result caching layer
- [ ] Write unit tests for each retriever
- [ ] Write integration tests with real APIs

---

## Phase 7 — Evidence, Ranking, Verification ⏳ NOT STARTED

- [ ] Implement `EvidenceAgent` (claim extraction)
- [ ] Implement evidence ranking algorithm
- [ ] Implement `VerificationAgent` (cross-reference claims)
- [ ] Implement URL validation and content fetching
- [ ] Implement confidence score assignment
- [ ] Implement contradiction detection
- [ ] Persist all claims and verification results to DB
- [ ] Write unit tests
- [ ] Write integration tests

---

## Phase 8 — Gap Analysis & Iterative Research ⏳ NOT STARTED

- [ ] Implement `GapAnalysisAgent`
- [ ] Implement gap detection logic (missing topics, conflicting claims)
- [ ] Implement iterative retrieval loop (gap → new research queries)
- [ ] Implement convergence threshold (when to stop iterating)
- [ ] Implement research depth configuration
- [ ] Write unit tests
- [ ] Write integration tests

---

## Phase 9 — Writer, Critic, Visualization ⏳ NOT STARTED

- [ ] Implement `WriterAgent` with structured section generation
- [ ] Implement full report schema (all required sections)
- [ ] Implement `CriticAgent` with evaluation rubrics
- [ ] Implement `VisualizationAgent` (tables, timelines, knowledge maps)
- [ ] Implement `ExportAgent` (PDF, Markdown, HTML, JSON)
- [ ] Write unit tests
- [ ] Write integration tests

---

## Phase 10 — Frontend ⏳ NOT STARTED

- [ ] Initialize React + Vite + TypeScript project
- [ ] Implement design system (dark/light mode, typography, colors)
- [ ] Implement Sidebar (history, saved reports, collections, templates)
- [ ] Implement Main Workspace (input, options, live progress)
- [ ] Implement SSE client for real-time agent activity timeline
- [ ] Implement Evidence Viewer component
- [ ] Implement Citation Viewer with confidence scores
- [ ] Implement Report Viewer with streaming output
- [ ] Implement Export controls (PDF, Markdown, JSON)
- [ ] Responsive layout
- [ ] Accessibility audit

---

## Phase 11 — Authentication, Database, History ⏳ NOT STARTED

- [ ] Implement JWT authentication middleware
- [ ] Implement user registration and login endpoints
- [ ] Implement research session ownership
- [ ] Implement research history API
- [ ] Implement saved reports API
- [ ] Implement collections API
- [ ] Implement rate limiting middleware
- [ ] Write security tests

---

## Phase 12 — Optimization, Testing, Deployment ⏳ NOT STARTED

- [ ] Full integration test suite
- [ ] Load testing (concurrent research sessions)
- [ ] Performance profiling and optimization
- [ ] Docker + Docker Compose setup
- [ ] Environment-specific configuration (dev/staging/prod)
- [ ] CI pipeline (lint, test, type-check)
- [ ] Deployment documentation
- [ ] Final README

---

*Document maintained by: Lead Architecture Review*
*Last updated: 2026-07-01*
