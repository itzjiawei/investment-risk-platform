"""initial schema

Revision ID: 20260706_0001
Revises:
Create Date: 2026-07-06
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260706_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            asset_id INTEGER PRIMARY KEY,
            ticker TEXT NOT NULL,
            name TEXT NOT NULL,
            sector TEXT NOT NULL,
            country TEXT NOT NULL,
            yfinance_ticker TEXT
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id INTEGER PRIMARY KEY,
            portfolio_name TEXT NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS holdings (
            portfolio_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (portfolio_id, asset_id),
            FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id),
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            asset_id INTEGER NOT NULL,
            date DATE NOT NULL,
            close_price DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (asset_id, date),
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id)
        )
        """
    )
    op.execute(
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
    op.execute(
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
    op.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS yfinance_ticker TEXT")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'viewer'")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prices_asset_date ON prices (asset_id, date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_email ON audit_logs (user_email)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_user_email")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_action")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_created_at")
    op.execute("DROP INDEX IF EXISTS ix_prices_asset_date")
    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS prices")
    op.execute("DROP TABLE IF EXISTS holdings")
    op.execute("DROP TABLE IF EXISTS portfolios")
    op.execute("DROP TABLE IF EXISTS assets")
