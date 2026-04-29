# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Claude Project Guidelines

You are a developer for the family expense tracker development. Your responsibilities:

- Develop code based on requirements in JIRA tickets
- Write unit tests for developed code/modules/methods
- Fix bugs and defects

## Development Guidelines

- Refer to **FamilyExpenseTracker_Wireframes_v1.1** and **Low_Level_Technical_Architecture_Family_Expense_Tracker_V1.2** in `project_resources/`
- Follow industry best practices for Python and React code

## GitHub Repository Guidelines

- Always create a feature branch from `master` before development
- Name feature branches with the JIRA ticket ID (e.g., `SCRUM-19`)


---

## Architecture Overview

Full-stack app: **FastAPI** backend + **React/Vite** frontend. They communicate via HTTP-only cookies for auth tokens (no `Authorization` headers).

### Backend (`backend/`)

- **Framework**: FastAPI with async SQLAlchemy 2.0 and aiomysql (MySQL in prod, aiosqlite in tests)
- **Config**: `app/config.py` — Pydantic `Settings` reads from `.env` (`DATABASE_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, etc.)
- **Database**: `app/database.py` — single async engine + session factory; `get_db` dependency yields a session per request
- **Auth flow**: Access token (JWT, 30 min) + refresh token (hashed SHA-256 in DB, 7 days) both delivered as HTTP-only cookies. Refresh token rotation on every `/auth/refresh` call.
- **Layer structure**:
  - `app/routers/` — HTTP endpoints only, delegate to services
  - `app/services/` — business logic (`auth_service.py`, `token_service.py`)
  - `app/models/` — SQLAlchemy ORM models (`User`, `Household`, `Category`, `RefreshToken`)
  - `app/schemas/` — Pydantic request/response models
  - `app/core/` — cross-cutting concerns: `security.py` (bcrypt), `exceptions.py`
  - `app/dependencies.py` — `get_current_user` FastAPI dependency (reads `access_token` cookie)

**Registration** is a two-step form: `RegisterStep1` (user credentials) + `RegisterStep2` (household setup). On successful register, a `Household` and 12 default `Category` rows are created atomically.

### Frontend (`frontend/`)

- **Stack**: React 18, TypeScript, Vite, Tailwind CSS
- **State**: Zustand `authStore` holds `user | null` + `isAuthenticated`. Initialized on app load via `GET /auth/me`.
- **API**: Axios client (`src/api/axiosClient.ts`) with `withCredentials: true`. A 401 interceptor clears auth state and redirects to `/login`.
- **Routing**: React Router v6. `ProtectedRoute` redirects unauthenticated users to `/login`; `PublicRoute` redirects authenticated users to `/dashboard`.
- **Forms**: react-hook-form + Zod for validation.
- **Multi-step register**: Step 1 data is passed via `location.state` to Step 2, then both are combined into a single `POST /auth/register` call.

### Alembic Migrations

Migrations live in `backend/alembic/versions/`. Run from the `backend/` directory:

```bash
cd backend
alembic upgrade head       # apply all migrations
alembic revision --autogenerate -m "description"  # generate new migration
```

---

## Commands

### Backend

All backend commands run from the `backend/` directory with the virtual environment active.

```bash
# Install dependencies
cd backend && poetry install

# Run dev server (requires .env with DATABASE_URL and SECRET_KEY)
cd backend && uvicorn app.main:app --reload --port 8000

# Run all tests
cd backend && pytest

# Run a single test file
cd backend && pytest tests/test_auth_routes.py

# Run a single test by name
cd backend && pytest tests/test_auth_routes.py::test_register_success
```

**Test setup**: Tests use in-memory SQLite (`aiosqlite`). `conftest.py` provides `db` (isolated session per test) and `client` (HTTPX `AsyncClient` with DB override). No `.env` needed for tests — env vars are set in `conftest.py`.

### Frontend

```bash
# Install dependencies
cd frontend && npm install

# Run dev server (proxies /auth/* to http://localhost:8000 via Vite config)
cd frontend && npm run dev

# Type-check + build
cd frontend && npm run build

# Run tests
cd frontend && npm test
```
# Guidlines to start the backend and frontend server

use start-servers.ps1 located in the project root to start the servers