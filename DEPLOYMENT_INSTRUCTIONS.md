# DSRA V2 — Cloud Deployment Guide

This guide explains how to deploy the entire **Deep Scientific Research Pipeline (DSRA V2)** to the cloud for free using:
1. **Neon.tech** (Serverless PostgreSQL Database)
2. **Render.com** (FastAPI Backend + ChromaDB Vector Store)
3. **Vercel** (React + Vite + TypeScript Frontend)

---

## 🗺️ Deployment Overview

```mermaid
graph TD
    user([User Web Browser])
    neon[(Neon Serverless DB)]
    render[Render Web Service]
    vercel[Vercel Frontend Host]
    openai[OpenAI API]

    user -->|1. Requests Assets| vercel
    user -->|2. Runs Research / Auth| render
    render -->|3. Persists Sessions & Reports| neon
    render -->|4. Runs AI Agents| openai
```

---

## 1. 🐘 Database Setup: Neon.tech

Neon provides a free serverless PostgreSQL database with autoscaling and branching capabilities.

### Steps:
1. Sign up at [Neon.tech](https://neon.tech/) (using GitHub or Google).
2. Create a new project:
   - **Name**: `dsra-v2`
   - **Postgres Version**: `16`
   - **Region**: Select the region closest to you (or closest to Render servers, e.g., US East / Oregon).
3. Copy the **Connection String** from the Neon dashboard. It will look like this:
   ```text
   postgresql://alex:abc123xyz@ep-cool-snowflake-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
   > [!IMPORTANT]
   > Make sure the connection string ends with `?sslmode=require`. Neon requires SSL for external connections.

---

## 2. 🚀 Backend API Setup: Render

Render will host the FastAPI server as a Dockerized Web Service. The Docker file in our repository is ready for production.

### Steps:
1. Sign up at [Render.com](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository containing the `dsra-v2` project.
4. Configure the Web Service settings:
   - **Name**: `dsra-backend`
   - **Region**: Select the same region you used in Neon (to reduce latency).
   - **Root Directory**: `backend` (Crucial! Render needs to look inside the `backend` subdirectory).
   - **Language**: `Docker`
   - **Branch**: `main` or your default branch.
   - **Instance Type**: `Free` (or Starter).
5. Open the **Advanced** section to add the following **Environment Variables**:

| Variable Name | Example Value | Description |
| :--- | :--- | :--- |
| `POSTGRES_USER` | `alex` | Extracted from your Neon connection string. |
| `POSTGRES_PASSWORD` | `abc123xyz` | Extracted from your Neon connection string. |
| `POSTGRES_HOST` | `ep-cool-snowflake-123456.us-east-2.aws.neon.tech` | Extracted from your Neon connection string. |
| `POSTGRES_PORT` | `5432` | Standard PostgreSQL port. |
| `POSTGRES_DB` | `neondb` | Database name from connection string. |
| `APP_SECRET_KEY` | *[Generate a 32-character random string]* | Key used for general cryptographic operations. |
| `JWT_SECRET_KEY` | *[Generate a 32-character random string]* | Key used to sign user JWT authorization tokens. |
| `OPENAI_API_KEY` | `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx` | Your actual OpenAI API key (required to run agents). |

6. Under **Docker Build Settings**:
   - Render automatically builds using the `backend/Dockerfile` since `Root Directory` is set to `backend`.
7. Click **Create Web Service**.

### 🔄 Database Migrations on Render:
To automatically apply the database tables and columns (including the new `visualization` fields) during build, add a **Pre-deploy Command** under the Render service settings:
```bash
alembic upgrade head
```
Or, you can run migrations manually by using Render's interactive shell once the container is deployed:
```bash
PYTHONPATH=. alembic upgrade head
```

---

## 3. 🌐 Frontend Setup: Vercel

Vercel will host the React single-page application.

### Steps:
1. Sign up at [Vercel.com](https://vercel.com/).
2. Click **Add New** -> **Project**.
3. Import your GitHub repository.
4. Configure the project:
   - **Root Directory**: `frontend` (Crucial! Tell Vercel to look inside the `frontend` subdirectory).
   - **Framework Preset**: `Vite` (automatically detected).
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Open the **Environment Variables** section and add:
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: `https://YOUR-RENDER-SERVICE-NAME.onrender.com` (Your deployed Render Web Service URL).
6. Click **Deploy**.

---

## 🛡️ Production Verification Checklist

Once all three parts are deployed, verify the workflow:
1. Load your Vercel URL in the browser.
2. In the sidebar, change **Execution Mode** to **Live Backend (API)**.
3. You should see the **Authenticate Workspace** glassmorphic modal.
4. Click **Need an account? Sign Up** to register a new user email and password.
   - This test checks Neon connectivity and FastAPI authentication router logic.
5. Once registered, type a query (e.g., `Therapeutic impact of Prime Editing in human hematopoietic cells`) and click **Initiate Deep Analysis**.
6. The terminal should stream live logs from the backend agents.
7. Once finished, check the **Knowledge Graph** and **Timeline** tabs to verify Neon retrieved the visualization data successfully.
