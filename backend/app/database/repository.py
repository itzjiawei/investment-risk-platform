from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from app.database.config import engine


def load_assets():
    query = text("SELECT * FROM assets")
    return pd.read_sql(query, engine)


def load_portfolios():
    query = text("SELECT * FROM portfolios")
    return pd.read_sql(query, engine)


def load_holdings():
    query = text("SELECT * FROM holdings")
    return pd.read_sql(query, engine)


def load_prices():
    query = text("SELECT * FROM prices")
    return pd.read_sql(query, engine)


def ensure_users_table():
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'viewer'
                """
            )
        )


def get_user_by_email(email: str):
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    user_id,
                    email,
                    full_name,
                    hashed_password,
                    role,
                    is_active
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        ).mappings().first()

    return dict(row) if row is not None else None


def create_user(
    email: str,
    full_name: str,
    hashed_password: str,
    role: str = "viewer",
    is_active: bool = True,
):
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (
                    email,
                    full_name,
                    hashed_password,
                    role,
                    is_active
                )
                VALUES (
                    :email,
                    :full_name,
                    :hashed_password,
                    :role,
                    :is_active
                )
                ON CONFLICT (email) DO NOTHING
                """
            ),
            {
                "email": email,
                "full_name": full_name,
                "hashed_password": hashed_password,
                "role": role,
                "is_active": is_active,
            },
        )


def update_user_role(email: str, role: str):
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE users
                SET role = :role
                WHERE email = :email
                """
            ),
            {
                "email": email,
                "role": role,
            },
        )


def list_users():
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    user_id,
                    email,
                    full_name,
                    role,
                    is_active
                FROM users
                ORDER BY user_id
                """
            )
        ).mappings().all()

    return [dict(row) for row in rows]


def ensure_audit_logs_table():
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    user_email TEXT,
                    user_role TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    status TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def insert_audit_log(
    user_id: int | None,
    user_email: str | None,
    user_role: str | None,
    action: str,
    resource_type: str | None,
    resource_id: str | None,
    status: str,
    ip_address: str | None,
    user_agent: str | None,
    metadata: str | None,
    created_at: datetime | None = None,
):
    ensure_audit_logs_table()
    created_at = created_at or datetime.now(timezone.utc).replace(tzinfo=None)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO audit_logs (
                    user_id,
                    user_email,
                    user_role,
                    action,
                    resource_type,
                    resource_id,
                    status,
                    ip_address,
                    user_agent,
                    metadata,
                    created_at
                )
                VALUES (
                    :user_id,
                    :user_email,
                    :user_role,
                    :action,
                    :resource_type,
                    :resource_id,
                    :status,
                    :ip_address,
                    :user_agent,
                    :metadata,
                    :created_at
                )
                """
            ),
            {
                "user_id": user_id,
                "user_email": user_email,
                "user_role": user_role,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "status": status,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "metadata": metadata,
                "created_at": created_at,
            },
        )


def list_audit_logs(
    action: str | None = None,
    user_email: str | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    limit: int = 100,
):
    ensure_audit_logs_table()

    filters = []
    params = {"limit": max(1, min(limit, 500))}

    if action:
        filters.append("action = :action")
        params["action"] = action

    if user_email:
        filters.append("user_email = :user_email")
        params["user_email"] = user_email

    if resource_type:
        filters.append("resource_type = :resource_type")
        params["resource_type"] = resource_type

    if status:
        filters.append("status = :status")
        params["status"] = status

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT
                    id,
                    user_id,
                    user_email,
                    user_role,
                    action,
                    resource_type,
                    resource_id,
                    status,
                    ip_address,
                    user_agent,
                    metadata,
                    created_at
                FROM audit_logs
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
                """
            ),
            params,
        ).mappings().all()

    return [
        _coerce_audit_log_row(dict(row))
        for row in rows
    ]


def _coerce_audit_log_row(row: dict):
    created_at = row.get("created_at")
    if isinstance(created_at, datetime) and created_at.tzinfo is None:
        row["created_at"] = created_at.replace(tzinfo=timezone.utc)

    return row
