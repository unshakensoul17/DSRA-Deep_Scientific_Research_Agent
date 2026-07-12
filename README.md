# DSRA V2 — Deep Scientific Research Agent Platform
=====================================================

DSRA V2 is an advanced, production-ready, asynchronous multi-agent platform designed to automate literature search, evidence extraction, claims verification, gap analysis, and compilation of academic-grade research reports.

---

## Key Features

- **Multi-Agent DAG Pipeline**: Planner -> Researcher -> Evidence Extraction -> Verification -> Gap Analysis -> Writer -> Critic -> Visualization -> Export.
- **Strict Fact Verification**: Cross-references claims against scientific databases (arXiv, PubMed, Semantic Scholar, Wikipedia) and scores confidence.
- **Self-Correction (Critique & Gap Loop)**: Agent revises draft and issues new targeted queries if coverage gaps are detected or quality thresholds are not met.
- **Asynchronous Execution & SSE Updates**: Runs parallel non-blocking research operations and streams real-time status updates via Server-Sent Events.
- **Advanced Export Formats**: Automatically compiles structured drafts into PDF (ReportLab), Markdown, HTML, and JSON packages.
- **Robust Authentication & Security**: Complete user isolation, JWT token refresh rotations, rate limiters, and clean database transaction rollbacks.

---

## Directory Structure

```text
dsra-v2/
├── .github/workflows/       # GitHub Actions CI configurations (lint, type-check, tests)
├── backend/                 # FastAPI & SQLAlchemy async server
│   ├── app/                 # Main application code (API, Core orchestrator, Agents, DB schemas)
│   ├── migrations/          # Alembic DB migration files
│   └── tests/               # Unit, integration, load, and profiling tests
├── frontend/                # React & Vite TypeScript client interface
├── docs/                    # Architecture diagrams, deployment documentation, and decisions
└── docker-compose.yml       # Production-ready services orchestration configuration
```

---

## Developer Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or Docker)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Initialize virtual environment and install dependencies:
   ```bash
   poetry install
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Launch FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Run local Vite development server:
   ```bash
   npm run dev
   ```

---

## Testing & Quality Control

### Run unit and integration tests:
```bash
cd backend
PYTHONPATH=. APP_SECRET_KEY=devkey123 POSTGRES_PASSWORD=password123 OPENAI_API_KEY=sk-test JWT_SECRET_KEY=jwtkey123 poetry run pytest -v
```

### Run concurrency load tests:
```bash
cd backend
PYTHONPATH=. APP_SECRET_KEY=devkey123 POSTGRES_PASSWORD=password123 OPENAI_API_KEY=sk-test JWT_SECRET_KEY=jwtkey123 poetry run python tests/load_test.py
```

### Run performance profiling:
```bash
cd backend
PYTHONPATH=. APP_SECRET_KEY=devkey123 POSTGRES_PASSWORD=password123 OPENAI_API_KEY=sk-test JWT_SECRET_KEY=jwtkey123 poetry run python tests/profile_orchestrator.py
```

---

## Deployment & Docker

To deploy the entire stack instantly using Docker Compose:
```bash
docker-compose up --build -d
```
Refer to the [Deployment & Operations Guide](docs/deployment.md) for Nginx configuration, SSL termination, and backup details.



Docker Compose commands you can use to build, start, stop, and debug the DSRA V2 environment.

1. Managing the Entire Stack
Start all containers in the background (detached mode):

bash
docker-compose up -d
(Starts the database dsra_db, backend dsra_backend, and frontend dsra_frontend in the correct dependency order).

Build and start all containers:

bash
docker-compose up -d --build
(Forces Docker to rebuild the backend and frontend Dockerfiles before starting).

Stop all running containers:

bash
docker-compose down
Stop all containers and remove persistent volumes (e.g. database reset):

bash
docker-compose down -v
2. Managing Specific Containers
If you are only editing frontend or backend code and don't want to rebuild or restart the entire database, you can target specific containers:

Rebuild and restart ONLY the frontend:

bash
docker-compose up -d --no-deps --build frontend
Rebuild and restart ONLY the backend:

bash
docker-compose up -d --no-deps --build backend
Restart a service without rebuilding:

bash
docker-compose restart frontend
3. Monitoring & Logs
Check the status of all running containers:

bash
docker ps
View live logs for the entire stack:

bash
docker-compose logs -f
View live logs for a specific service:

bash
docker-compose logs -f frontend
# OR
docker-compose logs -f backend
4. Database Interaction
Access the PostgreSQL CLI inside the database container:

bash
docker exec -it dsra_db psql -U postgres -d dsra_v2
Run database migrations manually inside the backend container:

bash
docker exec -it dsra_backend alembic upgrade head