import os

from dotenv import load_dotenv


load_dotenv()

DEFAULT_DATABASE_URL = (
    "postgresql://risk_user:risk_password@localhost:5433/risk_analytics"
)

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


def _get_csv_env(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name)

    if not raw_value:
        return default

    return [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]


def _get_cors_origins() -> list[str]:
    for name in ("CORS_ORIGINS", "FRONTEND_ORIGINS", "BACKEND_CORS_ORIGINS"):
        origins = _get_csv_env(name, [])
        if origins:
            return origins

    return DEFAULT_CORS_ORIGINS


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
CORS_ORIGINS = _get_cors_origins()
BACKEND_CORS_ORIGINS = CORS_ORIGINS
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
YFINANCE_REFRESH_PERIOD = os.getenv("YFINANCE_REFRESH_PERIOD", "1mo")
YFINANCE_BATCH_SIZE = int(os.getenv("YFINANCE_BATCH_SIZE", "20"))
YFINANCE_MAX_RETRIES = int(os.getenv("YFINANCE_MAX_RETRIES", "2"))
YFINANCE_RETRY_DELAY_SECONDS = float(
    os.getenv("YFINANCE_RETRY_DELAY_SECONDS", "1")
)
MARKET_REFRESH_ENABLED = _get_bool_env("MARKET_REFRESH_ENABLED", True)
MARKET_REFRESH_DAYS = os.getenv("MARKET_REFRESH_DAYS", "mon,tue,wed,thu,fri")
MARKET_REFRESH_HOUR_UTC = int(os.getenv("MARKET_REFRESH_HOUR_UTC", "22"))
MARKET_REFRESH_MINUTE_UTC = int(os.getenv("MARKET_REFRESH_MINUTE_UTC", "0"))
DB_SSLMODE = os.getenv("DB_SSLMODE")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
DEMO_USER_EMAIL = os.getenv("DEMO_USER_EMAIL", "demo@example.com")
DEMO_USER_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "demo123")
DEMO_USER_FULL_NAME = os.getenv("DEMO_USER_FULL_NAME", "Demo User")
NOTIFICATION_REPORT_RECIPIENTS = _get_csv_env(
    "NOTIFICATION_REPORT_RECIPIENTS",
    [],
)
