from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from app.database import engine
from app.services.auth_service import initialize_auth_storage


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def seed_assets() -> int:
    rows = _load_csv_rows(DATA_DIR / "assets.csv")

    with engine.begin() as connection:
        for row in rows:
            connection.execute(
                text(
                    """
                    UPDATE assets
                    SET
                        ticker = :ticker,
                        name = :name,
                        sector = :sector,
                        country = :country,
                        yfinance_ticker = :yfinance_ticker
                    WHERE asset_id = :asset_id
                    """
                ),
                row,
            )
            connection.execute(
                text(
                    """
                    INSERT INTO assets (
                        asset_id,
                        ticker,
                        name,
                        sector,
                        country,
                        yfinance_ticker
                    )
                    SELECT
                        :asset_id,
                        :ticker,
                        :name,
                        :sector,
                        :country,
                        :yfinance_ticker
                    WHERE NOT EXISTS (
                        SELECT 1 FROM assets WHERE asset_id = :asset_id
                    )
                    """
                ),
                row,
            )

    return len(rows)


def seed_portfolios() -> int:
    rows = _load_csv_rows(DATA_DIR / "portfolios.csv")

    with engine.begin() as connection:
        for row in rows:
            connection.execute(
                text(
                    """
                    UPDATE portfolios
                    SET portfolio_name = :portfolio_name
                    WHERE portfolio_id = :portfolio_id
                    """
                ),
                row,
            )
            connection.execute(
                text(
                    """
                    INSERT INTO portfolios (portfolio_id, portfolio_name)
                    SELECT :portfolio_id, :portfolio_name
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM portfolios
                        WHERE portfolio_id = :portfolio_id
                    )
                    """
                ),
                row,
            )

    return len(rows)


def seed_holdings() -> int:
    rows = _load_csv_rows(DATA_DIR / "holdings.csv")

    with engine.begin() as connection:
        for row in rows:
            connection.execute(
                text(
                    """
                    UPDATE holdings
                    SET quantity = :quantity
                    WHERE portfolio_id = :portfolio_id
                        AND asset_id = :asset_id
                    """
                ),
                row,
            )
            connection.execute(
                text(
                    """
                    INSERT INTO holdings (portfolio_id, asset_id, quantity)
                    SELECT :portfolio_id, :asset_id, :quantity
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM holdings
                        WHERE portfolio_id = :portfolio_id
                            AND asset_id = :asset_id
                    )
                    """
                ),
                row,
            )

    return len(rows)


def seed_prices() -> int:
    rows = _load_csv_rows(DATA_DIR / "prices.csv")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO prices (asset_id, date, close_price)
                VALUES (:asset_id, :date, :close_price)
                ON CONFLICT (asset_id, date) DO UPDATE
                SET close_price = EXCLUDED.close_price
                WHERE prices.close_price IS DISTINCT FROM EXCLUDED.close_price
                """
            ),
            rows,
        )

    return len(rows)


def _load_csv_rows(file_path: Path) -> list[dict[str, Any]]:
    dataframe = pd.read_csv(file_path)
    dataframe = dataframe.where(pd.notna(dataframe), None)
    return dataframe.to_dict(orient="records")


def main() -> None:
    print(f"Seeded assets: {seed_assets()} rows")
    print(f"Seeded portfolios: {seed_portfolios()} rows")
    print(f"Seeded holdings: {seed_holdings()} rows")
    print(f"Seeded prices: {seed_prices()} rows")

    initialize_auth_storage()
    print("Seeded demo users")

    print("Database seeded successfully")


if __name__ == "__main__":
    main()
