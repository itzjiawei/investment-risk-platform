# Architecture Diagrams

This document describes the current architecture of the Investment Risk Analytics Platform. Diagrams use Mermaid so they render directly on GitHub.

## 1. Overall System Architecture

```mermaid
flowchart LR
    Browser["User Browser"] --> Vite["React + TypeScript + Vite Frontend"]
    Vite --> API["FastAPI Backend"]

    API --> Auth["JWT Auth + RBAC Dependencies"]
    API --> Routers["API Routers"]
    API --> Scheduler["APScheduler Background Job"]

    Routers --> Services["Service Layer"]
    Scheduler --> MarketService["market_data_service"]
    Scheduler --> NotificationService["notification_service"]
    Scheduler --> AuditService["audit_service"]

    Services --> PortfolioService["portfolio_service"]
    Services --> AIService["ai_analysis_service + ollama_service"]
    Services --> PDFService["pdf_report_service"]
    Services --> PerformanceService["performance_service"]
    Services --> CacheService["dashboard_cache_service"]
    Services --> AuditService

    PortfolioService --> Repository["database.repository"]
    MarketService --> Repository
    AuditService --> Repository
    Auth --> Repository
    Repository --> Postgres["PostgreSQL / Neon"]

    MarketService --> Yahoo["Yahoo Finance via yfinance"]
    AIService --> Ollama["Local Ollama / Llama 3.2"]
    PerformanceService --> DuckDB["DuckDB Benchmarks"]
```

## 2. Frontend Page Architecture

```mermaid
flowchart TD
    Main["main.tsx"] --> App["App.tsx"]
    App --> Config["config.ts: API_BASE_URL"]
    App --> AuthState["Auth token + user role in localStorage"]
    App --> Axios["Axios default Authorization header"]

    App --> Login["LoginPage"]
    App --> Nav["Role-aware navigation"]

    Nav --> Dashboard["DashboardPage"]
    Nav --> Analytics["AnalyticsPage"]
    Nav --> Comparison["PortfolioComparisonPage"]
    Nav --> AICopilot["AiCopilotPage"]
    Nav --> Performance["PerformanceLab"]
    Nav --> Jobs["BackgroundJobsPage admin only"]
    Nav --> Audit["AuditLogsPage admin only"]

    Dashboard --> DashboardEndpoint["GET /api/portfolio/{id}/dashboard"]
    Dashboard --> RefreshEndpoint["POST /api/portfolio/{id}/market-data/refresh"]
    Dashboard --> PDFEndpoint["GET /api/portfolio/{id}/risk-report/pdf"]

    Analytics --> StressEndpoint["POST /api/portfolio/{id}/stress-test"]
    Comparison --> CompareEndpoint["POST /api/portfolio/compare"]
    AICopilot --> AIEndpoints["AI summary, chat, compare AI endpoints"]
    Performance --> PerfEndpoints["Performance and engine comparison endpoints"]
    Jobs --> JobEndpoints["GET /api/jobs/status + POST run-now"]
    Audit --> AuditEndpoint["GET /api/audit-logs"]
```

## 3. Backend Router, Service, and Database Architecture

```mermaid
flowchart TD
    Main["app.main:create_app"] --> CORS["CORSMiddleware"]
    Main --> Lifespan["FastAPI lifespan starts/stops scheduler"]
    Main --> HealthRouter["health.router"]
    Main --> AuthRouter["auth.router"]
    Main --> AuditRouter["audit.router"]
    Main --> JobsRouter["jobs.router"]
    Main --> NotificationsRouter["notifications.router"]
    Main --> MarketRouter["market_data.router"]
    Main --> PortfolioRouter["portfolio.router"]
    Main --> PerformanceRouter["performance.router"]
    Main --> AIRouter["ai.router"]

    AuthRouter --> AuthService["auth_service"]
    AuditRouter --> AuditService["audit_service"]
    JobsRouter --> JobService["market_refresh_job_service"]
    NotificationsRouter --> NotificationService["notification_service"]
    MarketRouter --> MarketService["market_data_service"]
    PortfolioRouter --> PortfolioService["portfolio_service"]
    PortfolioRouter --> DashboardCache["dashboard_cache_service"]
    PortfolioRouter --> PDFService["pdf_report_service"]
    PortfolioRouter --> PerformanceService["performance_service"]
    PerformanceRouter --> PerformanceService
    AIRouter --> AIAnalysis["ai_analysis_service"]

    AIAnalysis --> OllamaService["ollama_service"]
    JobService --> MarketService
    JobService --> DashboardCache
    JobService --> NotificationService
    NotificationService --> PDFService
    NotificationService --> PortfolioService

    AuthService --> Repository["database.repository"]
    AuditService --> Repository
    MarketService --> Repository
    PortfolioService --> Repository
    PerformanceService --> Repository
    PDFService --> PortfolioService

    Repository --> DBConfig["database.config engine"]
    DBConfig --> PostgreSQL["PostgreSQL"]
    Models["database.models"] --> Alembic["Alembic migrations"]
    Alembic --> PostgreSQL
```

## 4. Authentication and RBAC Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant AuthRouter as auth.router
    participant AuthService as auth_service
    participant DB as users table
    participant Protected as Protected endpoint
    participant Audit as audit_service

    User->>Frontend: Submit email and password
    Frontend->>AuthRouter: POST /api/auth/login
    AuthRouter->>AuthService: authenticate_user(email, password)
    AuthService->>DB: Load user by email
    DB-->>AuthService: User row with role and hashed password
    AuthService-->>AuthRouter: Authenticated user or None

    alt Login success
        AuthRouter->>Audit: create_audit_log(login success)
        AuthRouter-->>Frontend: JWT, token_type, email, full_name, role
        Frontend->>Frontend: Store token and role
    else Login failure
        AuthRouter->>Audit: create_audit_log(login failed)
        AuthRouter-->>Frontend: 401 Invalid email or password
    end

    Frontend->>Protected: Request with Authorization Bearer token
    Protected->>AuthService: get_current_user()
    AuthService->>DB: Resolve token subject to active user
    DB-->>AuthService: Current user
    Protected->>AuthService: require_roles(...)

    alt Role allowed
        Protected-->>Frontend: 200 response
    else Role denied
        AuthService->>Audit: create_audit_log(unauthorized_access)
        Protected-->>Frontend: 403 Insufficient permissions
    end
```

## 5. Market Data Refresh Flow

```mermaid
flowchart TD
    UserAction["User clicks Update Portfolio Prices"] --> Endpoint["POST /api/portfolio/{portfolio_id}/market-data/refresh"]
    AdminAction["Admin global refresh"] --> GlobalEndpoint["POST /api/market-data/refresh"]

    Endpoint --> Permission["require_market_refresh_permission admin or portfolio_manager"]
    GlobalEndpoint --> Permission
    Permission --> Service["market_data_service.refresh_market_data"]

    Service --> Assets["Load held assets from assets + holdings"]
    Assets --> TickerMap["Resolve yfinance_ticker or fallback ticker mapping"]
    TickerMap --> Dedupe["Deduplicate yfinance symbols"]
    Dedupe --> Batch["Batch downloads by YFINANCE_BATCH_SIZE"]
    Batch --> YFinance["Download daily history with yfinance.download"]

    YFinance --> Validate["Validate Close prices"]
    Validate --> Upsert["Update existing price dates and insert new dates"]
    Upsert --> Prices["prices table keyed by asset_id + date"]
    Upsert --> Summary["updated_tickers, failed_tickers, rows_inserted"]

    YFinance --> Retry["Retry failed batch with exponential backoff"]
    Retry --> YFinance
    Retry --> Failure["Batch or ticker still failed"]
    Failure --> FailedList["Append display ticker, yfinance ticker, reason"]
    FailedList --> Summary

    Summary --> CacheInvalidate["Invalidate dashboard cache"]
    Summary --> Audit["Audit market_data_refresh"]
    Summary --> Frontend["Show success plus failed ticker details"]
```

## 6. PDF Export Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant PortfolioRouter as portfolio.router
    participant Auth as auth_service
    participant PDF as pdf_report_service
    participant Portfolio as portfolio_service
    participant AI as ai_analysis_service
    participant Audit as audit_service

    Frontend->>PortfolioRouter: GET /api/portfolio/{id}/risk-report/pdf
    PortfolioRouter->>Auth: require_pdf_export_permission

    alt Role is admin, portfolio_manager, or analyst
        PortfolioRouter->>PDF: generate_pdf_risk_report(portfolio_id)
        PDF->>Portfolio: Risk, holdings, sector exposure, risk contribution, stress test
        PDF->>AI: Optional AI summary
        AI-->>PDF: AI summary or fallback note
        PDF-->>PortfolioRouter: PDF bytes
        PortfolioRouter->>Audit: create_audit_log(pdf_report_export success)
        PortfolioRouter-->>Frontend: application/pdf attachment
    else Viewer or unauthorized role
        Auth-->>Frontend: 403 Forbidden
    end
```

## 7. Background Scheduler Flow

```mermaid
flowchart TD
    Startup["FastAPI startup lifespan"] --> Config["Read MARKET_REFRESH_* config"]
    Config --> Enabled{"MARKET_REFRESH_ENABLED?"}
    Enabled -- "No" --> Disabled["Log scheduler disabled"]
    Enabled -- "Yes" --> Scheduler["Start APScheduler BackgroundScheduler UTC"]

    Scheduler --> Cron["Weekday cron trigger"]
    Cron --> Job["run_market_refresh_job(triggered_by=scheduler)"]
    RunNow["POST /api/jobs/market-refresh/run-now admin only"] --> Job

    Job --> Refresh["market_data_service.refresh_market_data()"]
    Refresh --> Cache["invalidate_all_dashboard_cache()"]
    Refresh --> Notifications["send_scheduled_daily_risk_reports(summary)"]
    Notifications --> ConsoleProvider["ConsoleNotificationProvider logs would-send report"]
    Job --> LastRun["Update in-memory last run status and summary"]
    Job --> Audit["Audit scheduled/run-now result"]

    Refresh --> Failure["Catch job-level exception"]
    Failure --> FailedStatus["Set failed last-run summary"]
    FailedStatus --> AuditFailed["Audit failed job without crashing FastAPI"]

    StatusEndpoint["GET /api/jobs/status"] --> LastRun
```

## 8. Deployment Architecture: Vercel to Render to Neon

```mermaid
flowchart LR
    Browser["User Browser"] --> Vercel["Vercel Frontend\nReact + Vite"]
    Vercel --> Render["Render Web Service\nFastAPI + Uvicorn"]
    Render --> Neon["Neon Postgres\nDATABASE_URL"]

    Render --> Yahoo["Yahoo Finance via yfinance"]
    Render -. "Local AI service, not part of Render deployment" .-> Ollama["Ollama"]

    GitHub["GitHub Repository"] --> Actions["GitHub Actions CI"]
    Actions --> BackendTests["Backend pytest"]
    Actions --> FrontendBuild["Frontend npm run build"]

    GitHub --> Vercel
    GitHub --> Render

    VercelEnv["Vercel env\nVITE_API_BASE_URL"] --> Vercel
    RenderEnv["Render env\nDATABASE_URL, CORS_ORIGINS, JWT_SECRET_KEY, DB_SSLMODE"] --> Render
```

## 9. Database and Table Relationship Overview

```mermaid
erDiagram
    PORTFOLIOS {
        int portfolio_id PK
        text portfolio_name
    }

    ASSETS {
        int asset_id PK
        text ticker
        text name
        text sector
        text country
        text yfinance_ticker
    }

    HOLDINGS {
        int portfolio_id PK, FK
        int asset_id PK, FK
        float quantity
    }

    PRICES {
        int asset_id PK, FK
        date date PK
        float close_price
    }

    USERS {
        int user_id PK
        text email UK
        text full_name
        text hashed_password
        text role
        boolean is_active
        timestamp created_at
    }

    AUDIT_LOGS {
        int id PK
        int user_id
        text user_email
        text user_role
        text action
        text resource_type
        text resource_id
        text status
        text ip_address
        text user_agent
        text metadata
        timestamp created_at
    }

    PORTFOLIOS ||--o{ HOLDINGS : contains
    ASSETS ||--o{ HOLDINGS : held_as
    ASSETS ||--o{ PRICES : has_prices
    USERS ||--o{ AUDIT_LOGS : produces
```

Note: `audit_logs.user_id` is stored for traceability but is not currently declared as a database-level foreign key in the migration.
