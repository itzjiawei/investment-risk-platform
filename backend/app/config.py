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


DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
CORS_ORIGINS = _get_cors_origins()
BACKEND_CORS_ORIGINS = CORS_ORIGINS
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
YFINANCE_REFRESH_PERIOD = os.getenv("YFINANCE_REFRESH_PERIOD", "1mo")
DB_SSLMODE = os.getenv("DB_SSLMODE")
