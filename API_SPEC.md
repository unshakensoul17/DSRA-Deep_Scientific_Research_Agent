# DSRA V2 — API Specification

> **Living Document** | Version: v1 | Last updated: 2026-07-01

Base URL: `/api/v1`
Auth: `Authorization: Bearer <jwt_token>` on all protected routes
Content-Type: `application/json`

---

## Authentication Routes

### POST `/auth/register`
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```
**Response `201`:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-07-01T00:00:00Z"
}
```
**Errors:** `400` (email taken), `422` (validation)

---

### POST `/auth/login`
Authenticate and receive JWT tokens.

**Request:**
```json
{ "email": "user@example.com", "password": "SecurePassword123!" }
```
**Response `200`:**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```
**Errors:** `401` (invalid credentials)

---

### POST `/auth/refresh`
Refresh access token using refresh token.

**Request:** `{ "refresh_token": "<jwt>" }`
**Response `200`:** `{ "access_token": "<jwt>", "expires_in": 3600 }`
**Errors:** `401` (expired/invalid refresh token)

---

## Research Session Routes

### POST `/research/sessions` 🔒
Create a new research session.

**Request:**
```json
{
  "topic": "The role of CRISPR-Cas9 in treating sickle cell disease",
  "depth": 2,
  "max_sources_per_query": 10,
  "source_preferences": ["arxiv", "semantic_scholar", "pubmed"],
  "focus_areas": ["clinical trials", "gene therapy mechanisms"],
  "max_iterations": 3
}
```
**Response `201`:**
```json
{
  "session_id": "uuid",
  "topic": "...",
  "state": "CREATED",
  "depth": 2,
  "created_at": "2026-07-01T00:00:00Z"
}
```

---

### GET `/research/sessions` 🔒
List all research sessions for the authenticated user.

**Query Params:**
- `state` — filter by session state (optional)
- `page` — page number (default: 1)
- `page_size` — results per page (default: 20, max: 100)
- `sort` — `created_at_desc` | `created_at_asc` (default: `created_at_desc`)

**Response `200`:**
```json
{
  "total": 42,
  "page": 1,
  "page_size": 20,
  "sessions": [
    {
      "session_id": "uuid",
      "topic": "...",
      "state": "COMPLETED",
      "created_at": "...",
      "completed_at": "..."
    }
  ]
}
```

---

### GET `/research/sessions/{session_id}` 🔒
Get detailed status of a specific session.

**Response `200`:**
```json
{
  "session_id": "uuid",
  "topic": "...",
  "state": "VERIFICATION",
  "depth": 2,
  "iteration_count": 1,
  "max_iterations": 3,
  "sources_count": 34,
  "claims_count": 18,
  "verified_claims_count": 15,
  "report_id": "uuid or null",
  "created_at": "...",
  "updated_at": "...",
  "agent_timeline": [
    {
      "agent": "PlannerAgent",
      "state": "PLANNING",
      "started_at": "...",
      "completed_at": "...",
      "duration_ms": 1240,
      "status": "SUCCESS"
    }
  ]
}
```
**Errors:** `404` (not found), `403` (not owner)

---

### POST `/research/sessions/{session_id}/start` 🔒
Start research execution for a session in CREATED state.

**Response `202`:**
```json
{
  "session_id": "uuid",
  "state": "PLANNING",
  "stream_url": "/api/v1/research/sessions/{session_id}/stream"
}
```
**Errors:** `409` (session not in CREATED state), `404`

---

### DELETE `/research/sessions/{session_id}` 🔒
Cancel a running session or delete a completed one.

**Response `200`:**
```json
{ "session_id": "uuid", "state": "CANCELLED" }
```
**Errors:** `404`, `403`

---

### GET `/research/sessions/{session_id}/stream` 🔒
**Server-Sent Events (SSE)** endpoint. Connect to receive real-time progress updates.

**Response:** `text/event-stream`

```
event: session_state_changed
data: {"session_id": "uuid", "state": "PLANNING", "timestamp": "..."}

event: agent_started
data: {"agent": "PlannerAgent", "session_id": "uuid", "timestamp": "..."}

event: agent_completed
data: {"agent": "PlannerAgent", "duration_ms": 1240, "timestamp": "..."}

event: source_batch_fetched
data: {"source_type": "arxiv", "count": 6, "total_so_far": 6}

event: evidence_extracted
data: {"evidence_count": 42, "session_id": "uuid"}

event: claim_verified
data: {"claim_id": "uuid", "status": "VERIFIED", "confidence": 0.87}

event: gap_detected
data: {"gaps": ["No clinical trial data found"], "will_iterate": true, "iteration": 2}

event: report_section_complete
data: {"section": "Background", "word_count": 487}

event: research_complete
data: {"session_id": "uuid", "report_id": "uuid", "total_duration_ms": 48230}

event: error
data: {"agent": "VerificationAgent", "message": "Rate limit hit", "retry_in_ms": 5000}
```

---

### GET `/research/sessions/{session_id}/sources` 🔒
Get all sources fetched for this session.

**Query Params:** `source_type`, `min_quality_score`, `page`, `page_size`

**Response `200`:**
```json
{
  "total": 34,
  "sources": [
    {
      "id": "uuid",
      "title": "...",
      "url": "...",
      "source_type": "arxiv",
      "quality_score": 0.89,
      "authors": ["Smith J.", "Doe A."],
      "year": 2023,
      "snippet": "...",
      "fetched_at": "..."
    }
  ]
}
```

---

### GET `/research/sessions/{session_id}/evidence` 🔒
Get extracted and verified claims for a session.

**Query Params:** `status` (VERIFIED|CONTRADICTED|UNVERIFIED), `min_confidence`, `page`, `page_size`

**Response `200`:**
```json
{
  "total": 18,
  "claims": [
    {
      "id": "uuid",
      "text": "CRISPR-Cas9 achieved 90% correction efficiency in HSC cells.",
      "confidence": 0.91,
      "status": "VERIFIED",
      "supporting_sources": 3,
      "contradicting_sources": 0,
      "reasoning": "..."
    }
  ]
}
```

---

## Report Routes

### GET `/reports/{report_id}` 🔒
Get the full generated report.

**Response `200`:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "title": "...",
  "executive_summary": "...",
  "sections": [
    {
      "title": "Background",
      "content": "...",
      "word_count": 487,
      "claim_ids": ["uuid1", "uuid2"]
    }
  ],
  "key_findings": ["Finding 1...", "Finding 2..."],
  "references": [
    {
      "citation_key": "[Frangoul, 2021]",
      "title": "...",
      "url": "...",
      "authors": ["Frangoul H."],
      "year": 2021,
      "source_type": "semantic_scholar"
    }
  ],
  "critique_score": 8.4,
  "status": "FINAL",
  "export_paths": {
    "pdf": "/api/v1/reports/uuid/export?format=pdf",
    "markdown": "/api/v1/reports/uuid/export?format=markdown"
  },
  "created_at": "...",
  "finalized_at": "..."
}
```

---

### GET `/reports/{report_id}/export` 🔒
Download the report in a specified format.

**Query Params:** `format` = `pdf` | `markdown` | `html` | `json`

**Response:** File download with appropriate Content-Type
- PDF: `application/pdf`
- Markdown: `text/markdown`
- HTML: `text/html`
- JSON: `application/json`

**Errors:** `404` (report not found), `400` (unsupported format)

---

### GET `/reports` 🔒
List all final reports for the authenticated user.

**Query Params:** `page`, `page_size`, `sort`

**Response `200`:**
```json
{
  "total": 12,
  "reports": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "title": "...",
      "executive_summary_snippet": "...",
      "status": "FINAL",
      "critique_score": 8.4,
      "created_at": "..."
    }
  ]
}
```

---

## Health & Diagnostics

### GET `/health`
Public health check endpoint.

**Response `200`:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-07-01T00:00:00Z",
  "components": {
    "database": "healthy",
    "vector_db": "healthy",
    "llm_gateway": "healthy"
  }
}
```

### GET `/health/ready`
Kubernetes readiness probe — returns `503` if any component is unavailable.

### GET `/health/live`
Kubernetes liveness probe — returns `200` if process is running.

---

## Error Response Schema

All errors follow this format:
```json
{
  "error": {
    "code": "RESEARCH_SESSION_NOT_FOUND",
    "message": "Research session with ID uuid was not found.",
    "details": {},
    "request_id": "uuid",
    "timestamp": "2026-07-01T00:00:00Z"
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Authenticated but not owner |
| `RESEARCH_SESSION_NOT_FOUND` | 404 | Session ID doesn't exist |
| `REPORT_NOT_FOUND` | 404 | Report ID doesn't exist |
| `SESSION_INVALID_STATE` | 409 | Cannot perform action in current state |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `INTERNAL_ERROR` | 500 | Unhandled server error |
| `LLM_GATEWAY_ERROR` | 503 | LLM provider unavailable |

---

## Rate Limits

| Route Group | Limit |
|-------------|-------|
| Auth routes | 10 req/min per IP |
| `POST /research/sessions` | 5 req/min per user |
| `POST /research/sessions/{id}/start` | 3 concurrent per user |
| All other authenticated routes | 60 req/min per user |

---

## OpenAPI

Full interactive documentation available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

*Document maintained by: Lead Architecture Review*
*Last updated: 2026-07-01*
