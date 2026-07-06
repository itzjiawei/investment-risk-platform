# Investment Risk Analytics Platform

[![CI](https://github.com/itzjiawei/investment-risk-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/itzjiawei/investment-risk-platform/actions/workflows/ci.yml)

A full-stack investment risk analytics platform that provides portfolio risk monitoring, stress testing, AI-powered risk analysis, portfolio comparison, and analytics benchmarking.

## Overview

This platform helps investment professionals analyze portfolio risk through:

- Portfolio risk metrics
- Portfolio performance tracking
- Free market data refresh with yfinance
- Sector exposure analysis
- Risk contribution attribution
- Custom stress testing
- AI-powered portfolio analysis
- Portfolio comparison
- Analytics engine benchmarking

## Features

### Dashboard

- Portfolio selection
- Market data refresh
- Portfolio value tracking
- Annualized return analysis
- Volatility analysis
- Sharpe ratio calculation
- Maximum drawdown monitoring
- Historical VaR monitoring
- Sector allocation visualization

### Analytics

- Holdings analysis
- Risk contribution attribution
- Custom stress testing
- Scenario analysis

### AI Copilot

- AI-generated risk summaries
- Natural language portfolio Q&A
- Conversation memory
- Portfolio insights

### PDF Risk Reports

- Downloadable portfolio risk report from the dashboard
- Includes key risk metrics, sector exposure, top risk contributors, stress test impact, and an optional AI summary
- Works without Ollama running by including a fallback AI-unavailable note

### Portfolio Comparison

- Side-by-side portfolio comparison
- Risk metric comparison
- AI-generated portfolio comparison analysis

### Performance Lab

- Analytics engine benchmarking
- PostgreSQL performance testing
- DuckDB performance testing
- Query execution comparison

---

## Architecture

Frontend:
- React
- TypeScript
- Vite
- Recharts
- Axios

Backend:
- FastAPI
- Python

Analytics:
- Pandas
- NumPy

Databases:
- PostgreSQL
- DuckDB

Market Data:
- yfinance
- Yahoo Finance

AI:
- Ollama
- Llama 3.2

---

## System Architecture

```mermaid
flowchart LR

    subgraph Frontend
        D[Dashboard]
        AN[Analytics]
        AI[AI Copilot]
        PC[Portfolio Comparison]
        PL[Performance Lab]
    end

    subgraph Backend
        API[FastAPI API]
        AE[Analytics Engine]
        CHAT[AI Chat Service]
    end

    subgraph Data
        PG[(PostgreSQL)]
        DD[(DuckDB)]
    end

    subgraph Market_Data
        YF[yfinance]
        YH[Yahoo Finance]
    end

    subgraph AI_System
        O[Ollama]
        L[Llama 3.2]
    end

    D --> API
    AN --> API
    AI --> API
    PC --> API
    PL --> API

    API --> AE
    API --> CHAT
    API --> YF

    AE --> PG
    AE --> DD
    YF --> YH
    YF --> PG

    PL -. Benchmark .-> PG
    PL -. Benchmark .-> DD

    CHAT --> O
    O --> L
```

---

## Project Structure

```text
investment-risk-platform/

backend/
├── .env.example
├── requirements.txt
├── seed_database.py
├── app/
│   ├── config.py
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── schemas/
│   └── database/
└── tests/

frontend/
├── .env.example
├── package.json
├── src/
│   ├── config.ts
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   ├── AiCopilotPage.tsx
│   │   ├── PortfolioComparisonPage.tsx
│   │   └── PerformanceLab.tsx
│   └── App.tsx

docker-compose.yml
.github/workflows/ci.yml
```

---

## Prerequisites

- Python 3.13, or another Python version compatible with the packages in `backend/requirements.txt`
- Node.js LTS
- Docker Desktop or Docker Engine for PostgreSQL
- Optional: Ollama with Llama 3.2 for local AI features

On Windows, run the same commands in PowerShell and activate the Python virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Environment Configuration

The project keeps sensible localhost defaults for development, but deployment values should come from environment variables.

Backend variables:

```text
DATABASE_URL=postgresql://risk_user:risk_password@localhost:5433/risk_analytics
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:3b
YFINANCE_REFRESH_PERIOD=1mo
MARKET_REFRESH_ENABLED=true
MARKET_REFRESH_DAYS=mon,tue,wed,thu,fri
MARKET_REFRESH_HOUR_UTC=22
MARKET_REFRESH_MINUTE_UTC=0
DB_SSLMODE=
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
DEMO_USER_EMAIL=demo@example.com
DEMO_USER_PASSWORD=demo123
DEMO_USER_FULL_NAME=Demo User
NOTIFICATION_REPORT_RECIPIENTS=
```

Frontend variables:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Copy the examples when setting up locally:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

For deployment, set `DATABASE_URL`, `CORS_ORIGINS`, and `VITE_API_BASE_URL` in the hosting provider. Do not commit real `.env` files.

---

## Docker Setup

Start PostgreSQL:

```bash
docker compose up -d postgres
```

The bundled Docker configuration exposes PostgreSQL on local port `5433`.

Run migrations, then seed or refresh demo database content if needed:

```bash
cd backend
alembic upgrade head
python seed_database.py
```

Stop the database:

```bash
docker compose down
```

---

## Running Locally

### Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python -m uvicorn app.main:app --reload
```

Backend runs on:

```text
http://127.0.0.1:8000
```

### Database Migrations

Alembic owns database schema creation and future schema changes. Seeding is separate: migrations create tables, while `seed_database.py` inserts or updates demo rows from CSV files.

Run migrations locally against Docker PostgreSQL:

```bash
cd backend
alembic upgrade head
```

Then seed demo data:

```bash
python seed_database.py
```

The seed script no longer replaces tables. It upserts assets, portfolios, holdings, and demo price rows so refreshed yfinance prices are not wiped by reseeding.

Create a future migration after changing SQLAlchemy models:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### Market Data Refresh

The platform ships with demo CSV data so the dashboard works locally without external services. You can optionally refresh portfolio prices from Yahoo Finance through the free `yfinance` package.

Run the backend, then use the dashboard button:

```text
Update Portfolio Prices
```

Or call the API directly:

```bash
curl -X POST http://127.0.0.1:8000/api/market-data/refresh
```

The dashboard refresh button updates only the selected portfolio's tickers. You can call the same portfolio-specific refresh endpoint directly:

```bash
curl -X POST http://127.0.0.1:8000/api/portfolio/1/market-data/refresh
```

The refresh process looks up tickers already used by the selected portfolio holdings, downloads recent daily close prices with yfinance, inserts only new price rows where possible, updates existing dates, and reports any failed tickers without stopping the whole refresh. Failed ticker responses include the display ticker, yfinance ticker, and reason.

The `assets` data includes both a display `ticker` and an optional `yfinance_ticker`. The frontend and analytics continue to show the display ticker, while market data refresh uses `yfinance_ticker` for exchange-specific symbols such as `DBS` -> `D05.SI`.

Portfolio holdings and sector exposure use each asset's latest valid available price. This keeps analytics stable when one ticker refreshes successfully but another ticker fails or has an older latest price.

The global refresh endpoint remains available if you want to refresh all held tickers:

```bash
curl -X POST http://127.0.0.1:8000/api/market-data/refresh
```

You can inspect the latest stored market data status with:

```bash
curl http://127.0.0.1:8000/api/market-data/status
```

### Scheduled Market Refresh

The backend also starts a lightweight APScheduler background job that refreshes all unique held tickers on a weekday UTC schedule. By default it runs Monday through Friday at `22:00 UTC`, intended to be after US market close while still being simple and free-tier friendly.

Scheduler environment variables:

```text
MARKET_REFRESH_ENABLED=true
MARKET_REFRESH_DAYS=mon,tue,wed,thu,fri
MARKET_REFRESH_HOUR_UTC=22
MARKET_REFRESH_MINUTE_UTC=0
```

The scheduled job reuses the same yfinance refresh service as the manual buttons, writes new price rows to PostgreSQL, skips duplicates where possible, invalidates the dashboard cache, and writes an audit log with updated tickers, failed tickers, and rows inserted. Ticker-level failures are captured in the summary and do not stop the rest of the refresh.

Admins can inspect scheduler state:

```bash
curl http://127.0.0.1:8000/api/jobs/status
```

Admins can trigger the scheduled all-ticker refresh manually:

```bash
curl -X POST http://127.0.0.1:8000/api/jobs/market-refresh/run-now
```

The frontend shows this in the admin-only Background Jobs tab. On Render free tier, scheduled jobs only run while the web service process is awake; if the service sleeps, the in-process scheduler will not execute until Render wakes the app again. For production-grade guaranteed scheduling, use an external cron/ping service or Render Cron Job later.

### Notifications

The app has a modular notification layer:

```text
NotificationService -> NotificationProvider -> ConsoleNotificationProvider
```

Schedulers and API routes call `NotificationService`; they do not depend on any specific vendor. The current provider is a console provider that logs that a report notification would have been sent, including recipient, report name, and attachment filename. This keeps the design open for future Slack, Teams, SMS, or paid email providers without changing scheduler logic.

Notification environment variables:

```text
NOTIFICATION_REPORT_RECIPIENTS=admin@example.com,manager@example.com
```

Manual testing:

1. Set `NOTIFICATION_REPORT_RECIPIENTS` in `backend/.env` if you want scheduled report notifications.
2. Start the backend and frontend.
3. Log in as an admin.
4. Open Background Jobs and use Send Test Report.
5. Check backend logs for the notification message.

The admin-only API endpoint is:

```text
POST /api/notifications/send-report
```

Example body:

```json
{
  "portfolio_id": 1,
  "recipient_email": "admin@example.com"
}
```

After a successful scheduled market refresh, the scheduler generates PDF risk reports for configured recipients and logs that the notifications would have been sent. Notification success/failure is audited without crashing the scheduler.

### Backend Tests

Install backend dependencies, including pytest:

```bash
cd backend
pip install -r requirements.txt
```

Run the automated backend tests:

```bash
cd backend
pytest
```

The tests use FastAPI `TestClient`. Database-dependent endpoints are tested by mocking the service/data-loading layer, so PostgreSQL does not need to be running. AI endpoints mock the Ollama-backed service responses, so Ollama does not need to be running.

### Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

Build the frontend for production:

```bash
cd frontend
npm run build
```

---

## PDF Export

Use the dashboard button:

```text
Download Risk Report
```

Or call the API directly:

```bash
curl -OJ http://127.0.0.1:8000/api/portfolio/1/risk-report/pdf
```

The PDF report includes core portfolio metrics, sector exposure, top risk contributors, stress test impact, and an AI summary when Ollama is available. If Ollama is not running, the report still downloads with an AI-unavailable note.

---

## AI Features

AI features call a local Ollama server by default:

```text
http://localhost:11434/api/generate
```

Install Ollama and pull the configured model if you want live local AI responses:

```bash
ollama pull llama3.2:3b
```

Set `OLLAMA_URL` and `OLLAMA_MODEL` if your Ollama server or model name differs. Backend tests mock AI responses and do not require Ollama.

---

## Authentication

The app uses a simple JWT login flow with role-based access control:

1. The frontend posts email/password to `POST /api/auth/login`.
2. The backend verifies the password with passlib/bcrypt.
3. The backend returns a bearer token and user role metadata.
4. The frontend stores the token in `localStorage` and sends it as:

```text
Authorization: Bearer <token>
```

Public endpoints:

- `GET /`
- `POST /api/auth/login`

Protected endpoints include portfolio analytics, market data, PDF export, AI, comparison, and performance routes.

RBAC roles:

| Role | Dashboard / Analytics / Comparison / Performance | AI Copilot | PDF Export | Update Portfolio Prices | Manage Users |
| --- | --- | --- | --- | --- | --- |
| `admin` | Yes | Yes | Yes | Yes | Yes |
| `portfolio_manager` | Yes | Yes | Yes | Yes | No |
| `analyst` | Yes | Yes | Yes | No | No |
| `viewer` | Yes | No | No | No | No |

Demo users:

```text
admin@example.com / admin123
manager@example.com / manager123
analyst@example.com / analyst123
viewer@example.com / viewer123
```

For backward-compatible local development, `demo@example.com / demo123` is also seeded as an admin by default. The JWT includes the user role, while backend permission dependencies still load the current user from the database before authorizing protected actions. Unauthenticated requests return `401`; authenticated users without the required role receive `403`.

For deployment, set a long random `JWT_SECRET_KEY` in Render and do not commit real secrets. The seed script creates the configurable demo user from `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`, and `DEMO_USER_FULL_NAME`, plus the role-specific demo users above.

---

## Audit Logging

The backend records database-backed audit logs for important user and system actions. This gives admins a review trail for security, operations, and finance/compliance style questions such as who exported a report, who refreshed market prices, and who attempted a restricted action.

Logged actions include:

- Successful and failed login attempts
- Market data refreshes
- PDF risk report exports
- AI risk summary generation
- AI Copilot questions
- AI portfolio comparison generation
- RBAC forbidden access attempts
- Admin user-list viewing

Audit logs are stored in the `audit_logs` table with fields for user id, email, role, action, resource type/id, status, IP address, user agent, metadata, and timestamp. Passwords and JWT tokens are not logged.

Admins can view recent logs in the frontend Audit Logs tab or through:

```text
GET /api/audit-logs
```

Optional filters are supported: `action`, `user_email`, `resource_type`, `status`, and `limit`. The endpoint is admin-only.

---

## GitHub Actions Locally

GitHub Actions runs in GitHub on every push and pull request. If you want to approximate the checks locally, run:

```bash
cd backend
pytest

cd ../frontend
npm run build
```

You can also use [`act`](https://github.com/nektos/act) to run workflows locally if it is installed:

```bash
act
```

---

## Troubleshooting

- Backend cannot connect to PostgreSQL: confirm `docker compose up -d postgres` is running and `DATABASE_URL` uses local port `5433`.
- Frontend cannot reach the API: confirm `VITE_API_BASE_URL` points to the running FastAPI server and `CORS_ORIGINS` includes the frontend origin.
- AI requests fail: confirm Ollama is running and the model in `OLLAMA_MODEL` is installed. PDF export still works without Ollama.
- Market data refresh returns failed tickers: yfinance/Yahoo Finance may return empty data for unavailable symbols or during network issues. Demo data remains available.
- CI build differs from local: run `pytest` from `backend/` and `npm run build` from `frontend/` before pushing.

---

## Deployment

Recommended free-tier friendly deployment:

- Frontend: Vercel
- Backend: Render web service
- Production database: Neon Postgres
- Local database: Docker PostgreSQL from `docker-compose.yml`

### Neon Postgres

1. Create a Neon project and database.
2. Copy the pooled or direct PostgreSQL connection string from Neon.
3. Use that value as Render's `DATABASE_URL`.
4. Do not commit the Neon URL or password.

Neon usually requires SSL. This app supports Neon SSL in two ways:

- If the Neon URL already includes `sslmode=require`, it is used as-is.
- If the host contains `neon.tech`, the backend automatically uses SSL.
- You can also set `DB_SSLMODE=require` explicitly on Render.

Run migrations against Neon from an environment where `DATABASE_URL` points to Neon:

```bash
cd backend
alembic upgrade head
```

Seed demo data only after migrations have created the schema:

```bash
python seed_database.py
```

Run these against Neon only after setting `DATABASE_URL` to the Neon connection string in the environment where the commands run. Do not commit Neon credentials.

### Render Backend

Use the included `render.yaml` blueprint or create a Render Web Service manually.

Render settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render environment variables:

```text
DATABASE_URL=<your Neon Postgres connection string>
CORS_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:5173,http://127.0.0.1:5173
DB_SSLMODE=require
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:3b
YFINANCE_REFRESH_PERIOD=1mo
MARKET_REFRESH_ENABLED=true
MARKET_REFRESH_DAYS=mon,tue,wed,thu,fri
MARKET_REFRESH_HOUR_UTC=22
MARKET_REFRESH_MINUTE_UTC=0
JWT_SECRET_KEY=<long random secret>
JWT_EXPIRE_MINUTES=480
DEMO_USER_EMAIL=demo@example.com
DEMO_USER_PASSWORD=<temporary demo password>
DEMO_USER_FULL_NAME=Demo User
NOTIFICATION_REPORT_RECIPIENTS=<comma-separated report recipients>
```

Health check endpoint:

```text
GET https://your-render-service.onrender.com/
```

Expected response:

```json
{"message":"Investment Risk Analytics API is running"}
```

### Vercel Frontend

Use the included `vercel.json` when deploying from the repository root.

Vercel settings:

```text
Framework Preset: Vite
Install Command: cd frontend && npm install
Build Command: cd frontend && npm run build
Output Directory: frontend/dist
```

Vercel environment variables:

```text
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

After changing `VITE_API_BASE_URL`, redeploy the frontend so Vite bakes the value into the production bundle.

### Local vs Production

- Local development uses Docker PostgreSQL on port `5433` by default.
- Production uses Neon through `DATABASE_URL`.
- Local frontend defaults to `http://127.0.0.1:8000`.
- Production frontend must set `VITE_API_BASE_URL` to the Render backend URL.
- Local AI can use Ollama on your machine.
- Render free tier usually will not run Ollama locally, so AI endpoints return a helpful fallback message when Ollama is unavailable. The rest of the analytics, PDF export, market data refresh, and dashboard continue to work.

### Deployment Checklist

- Neon database created.
- Render `DATABASE_URL` points to Neon.
- Render `CORS_ORIGINS` includes the Vercel frontend URL.
- Render start command uses `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Vercel `VITE_API_BASE_URL` points to the Render backend.
- Database has been seeded or migrated.
- The Neon `assets` table includes the optional `yfinance_ticker` column, or the database has been reseeded after pulling the latest data files.
- `GET /` on Render returns the health check JSON.
- Frontend dashboard loads portfolios from the deployed backend.
- PDF export downloads from the deployed backend.
- AI fallback message is acceptable for hosted deployment without Ollama.

### Deployment Troubleshooting

- CORS error in browser: add the exact Vercel domain to `CORS_ORIGINS` on Render, then redeploy or restart the Render service.
- Database SSL error: set `DB_SSLMODE=require` on Render or use a Neon connection string with `sslmode=require`.
- Render service starts but API data fails: confirm `DATABASE_URL` points to the seeded Neon database.
- Vercel still calls localhost: confirm `VITE_API_BASE_URL` is set in Vercel and redeploy the frontend.
- AI response says unavailable: expected on hosted Render without Ollama. Run Ollama locally for full AI behavior.

---

## Continuous Integration

Continuous Integration (CI) automatically validates the application whenever code is pushed or a pull request is opened. This project uses GitHub Actions to run backend and frontend checks in separate jobs so failures are easy to isolate.

The CI workflow runs on:
- `push`
- `pull_request`

The backend job:
- Sets up Python
- Installs dependencies from `backend/requirements.txt`
- Runs `pytest`

The frontend job:
- Sets up Node.js LTS
- Installs dependencies with `npm install`
- Runs `npm run build`

CI is useful because it catches broken tests, dependency issues, and TypeScript/build regressions before changes are merged.

---

## Example Capabilities

### Risk Monitoring

- Portfolio value tracking
- Volatility analysis
- Drawdown analysis
- Historical VaR analysis

### Stress Testing

Example scenario:

```text
Technology      -20%
Semiconductors  -30%
Financials      -10%
ETF             -15%
```

### AI Risk Analysis

Example questions:

- What is the biggest concentration risk?
- Which assets contribute the most risk?
- Is this portfolio sufficiently diversified?
- Summarize this portfolio for a risk committee.

---

## Future Roadmap

### Phase 1
- Portfolio risk analytics
- AI risk analyst
- Portfolio comparison

### Phase 2
- PDF report generation
- Real market data integration
- Historical backtesting

### Phase 3
- Multi-user support
- Portfolio optimization
- Compliance copilot
- Investment intelligence platform

---

## Author

Jia Wei
