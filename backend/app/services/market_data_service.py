from datetime import date
import logging
from time import sleep
from typing import Any

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.config import (
    YFINANCE_BATCH_SIZE,
    YFINANCE_MAX_RETRIES,
    YFINANCE_REFRESH_PERIOD,
    YFINANCE_RETRY_DELAY_SECONDS,
)
from app.database.config import engine


DEFAULT_REFRESH_PERIOD = YFINANCE_REFRESH_PERIOD
DEFAULT_BATCH_SIZE = max(1, YFINANCE_BATCH_SIZE)
DEFAULT_MAX_RETRIES = max(0, YFINANCE_MAX_RETRIES)
DEFAULT_RETRY_DELAY_SECONDS = max(0.0, YFINANCE_RETRY_DELAY_SECONDS)
logger = logging.getLogger(__name__)
_sleep = sleep

KNOWN_YFINANCE_TICKER_MAP = {
    "DBS": "D05.SI",
    "DBS.SI": "D05.SI",
    "OCBC": "O39.SI",
    "UOB": "U11.SI",
    "TENCENT": "0700.HK",
    "ALIBABA HK": "9988.HK",
    "ALIBABA": "9988.HK",
    "TSMC": "2330.TW",
}


def refresh_market_data(
    period: str = DEFAULT_REFRESH_PERIOD,
    portfolio_id: int | None = None,
) -> dict[str, Any]:
    assets = _get_relevant_assets(portfolio_id)

    updated_tickers: list[str] = []
    failed_tickers: list[dict[str, str]] = []
    rows_inserted = 0

    asset_requests = [
        {
            "asset_id": int(asset["asset_id"]),
            "ticker": str(asset["ticker"]),
            "yfinance_ticker": _get_yfinance_ticker(asset),
        }
        for asset in assets
    ]
    yfinance_tickers = [
        request["yfinance_ticker"]
        for request in asset_requests
    ]

    try:
        histories_by_ticker, download_failures, history_sources = _download_ticker_histories(
            yfinance_tickers,
            period,
        )
    except ImportError:
        for request in asset_requests:
            _record_failed_ticker(
                failed_tickers,
                request["ticker"],
                "yfinance is not installed or unavailable",
                request["yfinance_ticker"],
                category="dependency_unavailable",
                period=period,
            )
        return _build_refresh_summary(updated_tickers, failed_tickers, rows_inserted)

    for request in asset_requests:
        asset_id = request["asset_id"]
        ticker = request["ticker"]
        yfinance_ticker = request["yfinance_ticker"]

        if yfinance_ticker in download_failures:
            _record_failed_ticker(
                failed_tickers,
                ticker,
                download_failures[yfinance_ticker],
                yfinance_ticker,
                category="download_failed",
                period=period,
            )
            continue

        history = histories_by_ticker.get(yfinance_ticker)

        try:
            price_rows = _price_rows_from_history(asset_id, history)
        except Exception as exc:
            _record_failed_ticker(
                failed_tickers,
                ticker,
                str(exc),
                yfinance_ticker,
                category="invalid_response",
                period=period,
                source=history_sources.get(yfinance_ticker),
            )
            continue

        if not price_rows:
            _record_failed_ticker(
                failed_tickers,
                ticker,
                "No price data returned from yfinance",
                yfinance_ticker,
                category="empty_response",
                period=period,
                source=history_sources.get(yfinance_ticker),
            )
            continue

        try:
            inserted_count = _insert_new_price_rows(asset_id, price_rows)
        except Exception as exc:
            _record_failed_ticker(
                failed_tickers,
                ticker,
                f"Database insert failed: {exc}",
                yfinance_ticker,
                category="database_error",
                period=period,
                source=history_sources.get(yfinance_ticker),
            )
            continue

        if inserted_count > 0:
            updated_tickers.append(ticker)
            rows_inserted += inserted_count

    return _build_refresh_summary(updated_tickers, failed_tickers, rows_inserted)


def _build_refresh_summary(
    updated_tickers: list[str],
    failed_tickers: list[dict[str, str]],
    rows_inserted: int,
) -> dict[str, Any]:
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

    query_with_yfinance_ticker = text(
        f"""
        SELECT DISTINCT
            a.asset_id,
            a.ticker,
            a.yfinance_ticker
        FROM assets a
        INNER JOIN holdings h
            ON a.asset_id = h.asset_id
        {portfolio_filter}
        ORDER BY a.ticker
        """
    )
    query_without_yfinance_ticker = text(
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

    try:
        with engine.connect() as connection:
            rows = connection.execute(
                query_with_yfinance_ticker,
                query_params,
            ).mappings().all()
    except SQLAlchemyError:
        with engine.connect() as connection:
            rows = connection.execute(
                query_without_yfinance_ticker,
                query_params,
            ).mappings().all()

    return [dict(row) for row in rows]


def _fetch_price_rows(
    asset_id: int,
    ticker: str,
    period: str,
) -> list[dict[str, Any]]:
    history = _download_ticker_history(ticker, period)
    return _price_rows_from_history(asset_id, history)


def _price_rows_from_history(
    asset_id: int,
    history,
) -> list[dict[str, Any]]:
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


def _download_ticker_histories(
    tickers: list[str],
    period: str,
) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    unique_tickers = list(dict.fromkeys(tickers))
    histories_by_ticker = {}
    download_failures = {}
    history_sources = {}

    for ticker_batch in _chunked(unique_tickers, DEFAULT_BATCH_SIZE):
        try:
            downloaded = _download_tickers_with_retry(ticker_batch, period)
        except ImportError:
            raise
        except Exception as exc:
            reason = str(exc)
            for ticker in ticker_batch:
                download_failures[ticker] = reason
            continue

        for ticker in ticker_batch:
            history = _extract_history_for_ticker(
                downloaded,
                ticker,
            )
            source = "batch"

            if _is_empty_history(history):
                try:
                    history = _download_ticker_history_with_retry(ticker, period)
                    source = "individual_fallback"
                except Exception as exc:
                    download_failures[ticker] = str(exc)
                    continue

            histories_by_ticker[ticker] = history
            history_sources[ticker] = source

    return histories_by_ticker, download_failures, history_sources


def _download_tickers_with_retry(tickers: list[str], period: str):
    last_error: Exception | None = None

    for attempt in range(DEFAULT_MAX_RETRIES + 1):
        try:
            return _download_tickers(tickers, period)
        except Exception as exc:
            last_error = exc

            if attempt >= DEFAULT_MAX_RETRIES:
                break

            delay_seconds = DEFAULT_RETRY_DELAY_SECONDS * (2 ** attempt)
            logger.warning(
                "Market data batch download failed for %s on attempt %s/%s: %s. Retrying in %.2f seconds.",
                tickers,
                attempt + 1,
                DEFAULT_MAX_RETRIES + 1,
                exc,
                delay_seconds,
            )
            if delay_seconds > 0:
                _sleep(delay_seconds)

    if last_error is not None:
        raise last_error

    raise RuntimeError("Market data download failed without an exception")


def _download_ticker_history_with_retry(ticker: str, period: str):
    last_error: Exception | None = None

    for attempt in range(DEFAULT_MAX_RETRIES + 1):
        try:
            return _download_ticker_history(ticker, period)
        except Exception as exc:
            last_error = exc

            if attempt >= DEFAULT_MAX_RETRIES:
                break

            delay_seconds = DEFAULT_RETRY_DELAY_SECONDS * (2 ** attempt)
            logger.warning(
                "Market data individual fallback failed for %s on attempt %s/%s: %s. Retrying in %.2f seconds.",
                ticker,
                attempt + 1,
                DEFAULT_MAX_RETRIES + 1,
                exc,
                delay_seconds,
            )
            if delay_seconds > 0:
                _sleep(delay_seconds)

    if last_error is not None:
        raise last_error

    raise RuntimeError("Market data individual fallback failed without an exception")


def _download_tickers(tickers: list[str], period: str):
    yfinance = _get_yfinance_module()
    return yfinance.download(
        tickers=" ".join(tickers),
        period=period,
        interval="1d",
        auto_adjust=False,
        group_by="ticker",
        threads=False,
        progress=False,
    )


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


def _extract_history_for_ticker(downloaded, ticker: str):
    if downloaded is None or downloaded.empty:
        return pd.DataFrame()

    if isinstance(downloaded.columns, pd.MultiIndex):
        first_level = downloaded.columns.get_level_values(0)
        if ticker in first_level:
            return downloaded[ticker]

        second_level = downloaded.columns.get_level_values(1)
        if ticker in second_level:
            return downloaded.xs(ticker, axis=1, level=1)

        return pd.DataFrame()

    return downloaded


def _is_empty_history(history) -> bool:
    if history is None or history.empty:
        return True

    if "Close" not in history.columns:
        return True

    return history["Close"].dropna().empty


def _chunked(items: list[str], chunk_size: int):
    for index in range(0, len(items), chunk_size):
        yield items[index : index + chunk_size]


def _get_yfinance_ticker(asset: dict[str, Any]) -> str:
    yfinance_ticker = asset.get("yfinance_ticker")

    if yfinance_ticker is None or pd.isna(yfinance_ticker):
        return _map_display_ticker_to_yfinance(str(asset["ticker"]))

    cleaned_ticker = str(yfinance_ticker).strip()
    return cleaned_ticker or _map_display_ticker_to_yfinance(str(asset["ticker"]))


def _map_display_ticker_to_yfinance(ticker: str) -> str:
    cleaned_ticker = ticker.strip()
    return KNOWN_YFINANCE_TICKER_MAP.get(
        cleaned_ticker.upper(),
        cleaned_ticker,
    )


def _record_failed_ticker(
    failed_tickers: list[dict[str, str]],
    ticker: str,
    reason: str,
    yfinance_ticker: str,
    category: str,
    period: str,
    interval: str = "1d",
    source: str | None = None,
) -> None:
    logger.warning(
        "Market data refresh failed for %s using yfinance ticker %s category=%s period=%s interval=%s source=%s reason=%s",
        ticker,
        yfinance_ticker,
        category,
        period,
        interval,
        source,
        reason,
    )
    failed_tickers.append(
        {
            "ticker": ticker,
            "yfinance_ticker": yfinance_ticker,
            "reason": reason,
            "category": category,
            "period": period,
            "interval": interval,
            "source": source or "unknown",
        }
    )


def _insert_new_price_rows(
    asset_id: int,
    price_rows: list[dict[str, Any]],
) -> int:
    if not price_rows:
        return 0

    rows_to_upsert = [
        {
            **row,
            "asset_id": asset_id,
        }
        for row in price_rows
    ]

    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                INSERT INTO prices (asset_id, date, close_price)
                VALUES (:asset_id, :date, :close_price)
                ON CONFLICT (asset_id, date) DO UPDATE
                SET close_price = EXCLUDED.close_price
                WHERE prices.close_price IS DISTINCT FROM EXCLUDED.close_price
                RETURNING (xmax = 0) AS inserted
                """
            ),
            rows_to_upsert,
        )
        rows = result.mappings().all()

    return sum(1 for row in rows if row["inserted"])


def _to_date_string(value: Any) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if hasattr(value, "date"):
        return value.date().isoformat()

    return str(value)[:10]
