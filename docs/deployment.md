# DSRA V2 — Deployment & Operations Guide
==========================================

This document details the configuration, build, security, and deployment procedures for the Deep Scientific Research Agent (DSRA) platform version 2.

---

## 1. Architectural Overview

The DSRA V2 stack is structured as three primary service layers:
1. **Frontend**: Single Page React/TypeScript application bundled by Vite and served via Nginx.
2. **Backend**: FastAPI web server running ASGI workers via Uvicorn, coordinating the multi-agent DAG pipeline.
3. **Database**: PostgreSQL (v16) for structured research session logs, user metadata, audit records, and generated reports.
4. **Vector DB**: ChromaDB for embedding storage and claim semantic search (can run embedded or standalone).

---

## 2. Environment Configuration

All configurations are driven by environment variables. At startup, the backend validates variables using Pydantic Settings.

### Configuration Reference Table

| Variable | Type | Default | Environment | Description |
| :--- | :--- | :--- | :--- | :--- |
| `APP_ENV` | `string` | `development` | All | Deployment environment: `development`, `staging`, `production`. |
| `APP_DEBUG` | `bool` | `false` | Dev | Enables traceback outputs and verbose server details. |
| `APP_SECRET_KEY` | `string` | (Required) | All | Cryptographic signing key for API components. Must be 32+ characters. |
| `JWT_SECRET_KEY` | `string` | (Required) | All | Cryptographic secret key for signing JWT tokens. |
| `POSTGRES_HOST` | `string` | `localhost` | All | PostgreSQL server address. |
| `POSTGRES_DB` | `string` | `dsra_v2` | All | Target database name. |
| `POSTGRES_USER` | `string` | `dsra_user` | All | Database username. |
| `POSTGRES_PASSWORD`| `string` | (Required) | All | Database password (minimum 8 characters). |
| `OPENAI_API_KEY` | `string` | (Required) | All | Access key for GPT-4o research completion models. |

---

## 3. Docker-Compose Local Deployment

To launch the complete stack locally (or on a single staging server) using Docker:

### Step 1: Clone and Configure Environment Files
Prepare the configuration file from the template:
```bash
cp backend/.env.staging .env
```
Edit `.env` to supply the actual production-grade secrets, particularly `APP_SECRET_KEY`, `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, and `OPENAI_API_KEY`.

### Step 2: Spin Up Services
Run the command below to build custom backend and frontend images and launch PostgreSQL:
```bash
docker-compose up --build -d
```

### Step 3: Database Migrations
Run Alembic migrations inside the running backend container to construct database tables:
```bash
docker-compose exec backend alembic upgrade head
```

---

## 4. Production Deployment Best Practices

### A. Reverse Proxy (Nginx) and TLS Termination
It is highly recommended to place Nginx or Caddy in front of the docker services to terminate SSL.

**Nginx Virtual Host Config Example:**
```nginx
server {
    listen 443 ssl http2;
    server_name dsra.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/dsra.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dsra.yourdomain.com/privkey.pem;

    # Frontend Static Assets
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/v1/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SSE Event Streaming (Disable Buffering)
    location /api/v1/research/stream/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
        read_timeout 600s;
    }
}
```

### B. Security & Rate Limiting
- **CORS Configuration**: In `backend/app/config/settings.py`, restrict `CORS_ORIGINS` strictly to the frontend domain name.
- **SlowAPI**: Rate limiters protect `/auth` endpoints at 10 requests per minute and `/research/session` at 5 sessions per minute. Keep rate limiting enabled to prevent LLM API billing exhaustion.

### C. Automated Backups (PostgreSQL)
Implement a daily cron job to dump database contents to an external volume:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/dsra"
DATE=$(date +\%F-\%H\%M\%S)
docker exec dsra_db pg_dump -U postgres dsra_v2 > "$BACKUP_DIR/dsra_backup_$DATE.sql"
# Retain backups for 14 days
find "$BACKUP_DIR" -type f -name "*.sql" -mtime +14 -delete
```
