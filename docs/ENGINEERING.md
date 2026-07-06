# Engineering Guide

This document explains the repository layout and the responsibility of each major backend and frontend module.

## Repository Structure

```text
investment-risk-platform/
├── backend/              FastAPI API, analytics services, database access, tests
├── frontend/             React + TypeScript + Vite application
├── data/                 Demo seed data used by local setup
├── docs/                 Engineering and architecture documentation
├── .github/workflows/    GitHub Actions CI workflow
├── docker-compose.yml    Local PostgreSQL service
├── render.yaml           Render backend blueprint
└── vercel.json           Vercel frontend build configuration
```

## Backend Folders

- `backend/app/main.py`: FastAPI application factory, CORS configuration, router registration, and scheduler lifecycle.
- `backend/app/routers/`: HTTP route definitions. Routers should stay thin and delegate calculations or persistence to services.
- `backend/app/services/`: Business logic for analytics, AI, market refresh, PDF generation, notifications, audit logging, auth, caching, and scheduled jobs.
- `backend/app/schemas/`: Pydantic request and response models for API validation.
- `backend/app/database/`: SQLAlchemy engine configuration, ORM models, and repository functions.
- `backend/alembic/`: Alembic migration environment and versioned schema migrations.
- `backend/tests/`: Pytest regression tests using FastAPI `TestClient`.

Compatibility modules such as `backend/app/analytics.py`, `backend/app/ai_chat.py`, `backend/app/ai_service.py`, and `backend/app/data_loader.py` re-export service functions for older imports. New code should import from `app.services` or `app.database` directly.

## Backend Services

- `portfolio_service.py`: Portfolio value, returns, risk metrics, holdings, sector exposure, risk contribution, stress testing, and portfolio comparison.
- `market_data_service.py`: yfinance refresh logic, ticker mapping, price upsert behavior, failed ticker reporting, and market data status.
- `dashboard_cache_service.py`: Short-lived in-memory cache for consolidated dashboard analytics.
- `ai_analysis_service.py`: AI summary, AI Q&A, and AI comparison orchestration.
- `ollama_service.py`: Local Ollama HTTP integration and graceful fallback handling.
- `pdf_report_service.py`: ReportLab PDF risk report generation.
- `performance_service.py`: Pandas, PostgreSQL, and DuckDB benchmark helpers.
- `auth_service.py`: Password hashing, JWT creation/verification, seeded demo users, and RBAC dependencies.
- `audit_service.py`: Non-blocking audit log creation and audit log retrieval.
- `market_refresh_job_service.py`: APScheduler setup, run-now flow, last-run status, cache invalidation, and scheduled refresh audit logging.
- `notification_service.py`: Generic notification abstraction. The current provider logs report notifications through `ConsoleNotificationProvider`.

## Frontend Folders

- `frontend/src/App.tsx`: App shell, auth state, routing between page-level views, shared dashboard data loading.
- `frontend/src/pages/`: Feature pages for dashboard, analytics, AI copilot, comparison, performance lab, login, audit logs, and background jobs.
- `frontend/src/config.ts`: Frontend runtime configuration, including `VITE_API_BASE_URL`.
- `frontend/src/App.css` and `frontend/src/index.css`: Application styling.
- `frontend/public/`: Static browser assets such as favicon and icon sprite.

The frontend currently uses page-level components rather than a shared component library. If the UI grows, reusable controls can move into `frontend/src/components/`, API wrappers into `frontend/src/services/`, and auth helpers into `frontend/src/contexts/`.

## Database Tables

- `assets`: Asset metadata, display ticker, sector, country, and optional yfinance ticker.
- `portfolios`: Portfolio identifiers and names.
- `holdings`: Portfolio-to-asset quantities.
- `prices`: Historical close prices keyed by `asset_id` and `date`.
- `users`: Login users, hashed passwords, active flag, and RBAC role.
- `audit_logs`: Security and operations audit trail for login, refresh, export, AI, forbidden access, and admin actions.

## Scheduler

The in-process APScheduler job starts with the FastAPI lifespan hook when `MARKET_REFRESH_ENABLED=true`. It refreshes all held tickers using the same market data service as manual refresh, invalidates dashboard cache, writes audit logs, records last-run status, and triggers console notification flow for configured report recipients.

Render free-tier services may sleep, so this scheduler is best-effort in hosted deployments on that tier. Deployments that require guaranteed execution should use Render Cron Jobs or another external scheduler.

## Middleware

The backend currently uses FastAPI's CORS middleware. Allowed origins come from `CORS_ORIGINS`, `FRONTEND_ORIGINS`, or `BACKEND_CORS_ORIGINS`, with localhost defaults for development. Auth and RBAC are implemented as FastAPI dependencies rather than middleware so endpoint permissions remain explicit.

## Configuration Files

- `backend/.env.example`: Backend environment variable template.
- `frontend/.env.example`: Frontend environment variable template.
- `docker-compose.yml`: Local PostgreSQL service on host port `5433`.
- `render.yaml`: Render backend service blueprint.
- `vercel.json`: Vercel frontend build/output settings.
- `.github/workflows/ci.yml`: Backend pytest and frontend build pipeline.
- `backend/alembic.ini`: Alembic configuration.
- `frontend/package.json`: Frontend scripts and dependencies.
- `backend/requirements.txt`: Backend Python dependencies.

## Development Rules

- Keep API response shapes stable unless a deliberate versioned change is made.
- Keep routers thin and put business logic in services.
- Use Alembic for schema changes, then seed data with `seed_database.py`.
- Do not run tests against Neon production unless intentional; tests mock audit logging by default to avoid writing operational audit rows.
- Do not commit `.env` files, generated reports, caches, build output, or real credentials.
