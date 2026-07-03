from sqlalchemy import create_engine

from app.config import DATABASE_URL, DB_SSLMODE


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)

    return database_url


def _get_connect_args(database_url: str) -> dict[str, str]:
    if DB_SSLMODE:
        return {"sslmode": DB_SSLMODE}

    if "neon.tech" in database_url and "sslmode=" not in database_url:
        return {"sslmode": "require"}

    return {}


DATABASE_URL = _normalize_database_url(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args=_get_connect_args(DATABASE_URL),
    pool_pre_ping=True,
)
