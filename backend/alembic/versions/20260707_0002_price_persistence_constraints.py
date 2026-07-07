"""price persistence constraints and indexes

Revision ID: 20260707_0002
Revises: 20260706_0001
Create Date: 2026-07-07
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260707_0002"
down_revision: Union[str, None] = "20260706_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM prices
        WHERE asset_id IS NULL
            OR date IS NULL
            OR close_price IS NULL
        """
    )
    op.execute(
        """
        DELETE FROM prices p
        USING (
            SELECT
                ctid,
                ROW_NUMBER() OVER (
                    PARTITION BY asset_id, date
                    ORDER BY
                        (close_price IS NOT NULL) DESC,
                        ctid DESC
                ) AS row_number
            FROM prices
        ) ranked
        WHERE p.ctid = ranked.ctid
            AND ranked.row_number > 1
        """
    )
    op.execute("ALTER TABLE prices ALTER COLUMN asset_id SET NOT NULL")
    op.execute("ALTER TABLE prices ALTER COLUMN date SET NOT NULL")
    op.execute("ALTER TABLE prices ALTER COLUMN close_price SET NOT NULL")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = current_schema()
                    AND tablename = 'prices'
                    AND indexdef ILIKE '%UNIQUE%'
                    AND indexdef ILIKE '%(asset_id, date)%'
            ) THEN
                ALTER TABLE prices
                ADD CONSTRAINT uq_prices_asset_id_date
                UNIQUE (asset_id, date);
            END IF;
        END $$;
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_prices_asset_date")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prices_date ON prices (date)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_prices_date")
    op.execute("ALTER TABLE prices DROP CONSTRAINT IF EXISTS uq_prices_asset_id_date")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prices_asset_date ON prices (asset_id, date)")
