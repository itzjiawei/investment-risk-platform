from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import text

from app.config import YFINANCE_REFRESH_PERIOD
from app.database.config import engine


DEFAULT_REFRESH_PERIOD = YFINANCE_REFRESH_PERIOD


def refresh_market_data(
    period: str = DEFAULT_REFRESH_PERIOD,
    portfolio_id: int | None = None,
) -> dict[str, Any]:
    assets = _get_relevant_assets(portfolio_id)

    updated_tickers: list[str] = []
    failed_tickers: list[dict[str, str]] = []
    rows_inserted = 0

    for asset in assets:
        asset_id = int(asset["asset_id"])
        ticker = str(asset["ticker"])

        try:
            price_rows = _fetch_price_rows(asset_id, ticker, period)
        except ImportError:
            failed_tickers.append(
                {
                    "ticker": ticker,
                    "reason": "yfinance is not installed or unavailable",
                }
            )
            continue
        except Exception as exc:
            failed_tickers.append(
                {
                    "ticker": ticker,
                    "reason": str(exc),
                }
            )
            continue

        if not price_rows:
            failed_tickers.append(
                {
                    "ticker": ticker,
                    "reason": "No price data returned",
                }
            )
            continue

        try:
            inserted_count = _insert_new_price_rows(asset_id, price_rows)
        except Exception as exc:
            failed_tickers.append(
                {
                    "ticker": ticker,
                    "reason": f"Database insert failed: {exc}",
                }
            )
            continue

        if inserted_count > 0:
            updated_tickers.append(ticker)
            rows_inserted += inserted_count

    return {
        "updated_tickers": updated_tickers,
        "failed_tickers": failed_tickers,
        "rows_inserted": rows_inserted,
        "message": "Market data refresh completed",
    }


def get_market_data_status() -> dict[str, Any]:
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    COUNT(*) AS price_rows,
                    MAX(date) AS latest_price_date
                FROM prices
                """
            )
        ).mappings().one()

    latest_price_date = result["latest_price_date"]

    return {
        "latest_price_date": (
            _to_date_string(latest_price_date)
            if latest_price_date is not None
            else None
        ),
        "price_rows": int(result["price_rows"]),
    }


def _get_relevant_assets(portfolio_id: int | None = None) -> list[dict[str, Any]]:
    query_params = {}

    portfolio_filter = ""

    if portfolio_id is not None:
        portfolio_filter = "WHERE h.portfolio_id = :portfolio_id"
        query_params["portfolio_id"] = portfolio_id

    query = text(
        f"""
        SELECT DISTINCT
            a.asset_id,
            a.ticker
        FROM assets a
        INNER JOIN holdings h
            ON a.asset_id = h.asset_id
        {portfolio_filter}
        ORDER BY a.ticker
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query, query_params).mappings().all()

    return [dict(row) for row in rows]


def _fetch_price_rows(
    asset_id: int,
    ticker: str,
    period: str,
) -> list[dict[str, Any]]:
    history = _download_ticker_history(ticker, period)

    if history is None or history.empty:
        return []

    if "Close" not in history.columns:
        raise ValueError("Downloaded data does not include Close prices")

    close_prices = history[["Close"]].dropna()

    rows = []

    for index, row in close_prices.iterrows():
        close_price = row["Close"]

        if pd.isna(close_price):
            continue

        rows.append(
            {
                "asset_id": asset_id,
                "date": _to_date_string(index),
                "close_price": round(float(close_price), 2),
            }
        )

    return rows


def _download_ticker_history(ticker: str, period: str):
    yfinance = _get_yfinance_module()
    return yfinance.Ticker(ticker).history(
        period=period,
        interval="1d",
        auto_adjust=False,
    )


def _get_yfinance_module():
    import yfinance

    return yfinance


def _insert_new_price_rows(
    asset_id: int,
    price_rows: list[dict[str, Any]],
) -> int:
    existing_dates = _get_existing_price_dates(asset_id)
    existing_rows = [
        row
        for row in price_rows
        if row["date"] in existing_dates
    ]
    new_rows = [
        row
        for row in price_rows
        if row["date"] not in existing_dates
    ]

    if not new_rows and not existing_rows:
        return 0

    with engine.begin() as connection:
        if existing_rows:
            connection.execute(
                text(
                    """
                    UPDATE prices
                    SET close_price = :close_price
                    WHERE asset_id = :asset_id
                        AND date = :date
                    """
                ),
                existing_rows,
            )

        if new_rows:
            connection.execute(
                text(
                    """
                    INSERT INTO prices (asset_id, date, close_price)
                    VALUES (:asset_id, :date, :close_price)
                    """
                ),
                new_rows,
            )

    return len(new_rows)


def _get_existing_price_dates(asset_id: int) -> set[str]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT date FROM prices WHERE asset_id = :asset_id"),
            {"asset_id": asset_id},
        ).all()

    return {
        _to_date_string(row[0])
        for row in rows
    }


def _to_date_string(value: Any) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if hasattr(value, "date"):
        return value.date().isoformat()

    return str(value)[:10]
