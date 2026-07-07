from pathlib import Path
import time

import duckdb
import pandas as pd

from app.database.repository import load_holdings, load_prices
from app.services.portfolio_service import calculate_portfolio_value


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"


def calculate_portfolio_value_duckdb(portfolio_id: int):
    prices = load_prices()
    holdings = load_holdings()

    con = duckdb.connect(database=":memory:")

    con.register("prices", prices)
    con.register("holdings", holdings)

    result = con.execute(
        """
        SELECT
            p.date,
            ROUND(SUM(p.close_price * h.quantity), 2) AS portfolio_value
        FROM prices p
        JOIN holdings h
            ON p.asset_id = h.asset_id
        WHERE h.portfolio_id = ?
        GROUP BY p.date
        ORDER BY p.date
        """,
        [portfolio_id],
    ).fetchdf()

    return result.to_dict(orient="records")


def compare_analytics_engines(portfolio_id: int):
    start = time.perf_counter()
    pandas_result = calculate_portfolio_value(portfolio_id)
    pandas_time = time.perf_counter() - start

    start = time.perf_counter()
    duckdb_result = calculate_portfolio_value_duckdb(portfolio_id)
    duckdb_time = time.perf_counter() - start

    speedup = pandas_time / duckdb_time if duckdb_time > 0 else 0

    return {
        "portfolio_id": portfolio_id,
        "pandas_rows": len(pandas_result),
        "pandas_time_seconds": round(pandas_time, 6),
        "duckdb_rows": len(duckdb_result),
        "duckdb_time_seconds": round(duckdb_time, 6),
        "duckdb_speedup": round(speedup, 2),
    }


def run_large_dataset_benchmark():
    large_prices = DATA_DIR / "large_prices.csv"
    large_holdings = DATA_DIR / "large_holdings.csv"

    missing_files = [
        str(path)
        for path in (large_prices, large_holdings)
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Large benchmark data files are missing: "
            + ", ".join(missing_files)
        )

    start = time.perf_counter()

    prices = pd.read_csv(large_prices)
    holdings = pd.read_csv(large_holdings)

    merged = prices.merge(
        holdings,
        on="asset_id",
        how="inner",
    )

    merged["market_value"] = merged["close_price"] * merged["quantity"]

    merged.groupby("date")["market_value"].sum().reset_index()

    pandas_time = time.perf_counter() - start

    start = time.perf_counter()

    con = duckdb.connect(database=":memory:")

    duckdb_result = con.execute(
        """
        SELECT
            p.date,
            SUM(p.close_price * h.quantity) AS portfolio_value
        FROM read_csv_auto(?) p
        JOIN read_csv_auto(?) h
            ON p.asset_id = h.asset_id
        GROUP BY p.date
        ORDER BY p.date
        """,
        [str(large_prices), str(large_holdings)],
    ).fetchdf()

    duckdb_time = time.perf_counter() - start

    speedup = pandas_time / duckdb_time if duckdb_time > 0 else 0

    return {
        "dataset": "large synthetic portfolio dataset",
        "price_rows": int(len(prices)),
        "holding_rows": int(len(holdings)),
        "output_rows": int(len(duckdb_result)),
        "pandas_time_seconds": round(float(pandas_time), 6),
        "duckdb_time_seconds": round(float(duckdb_time), 6),
        "duckdb_speedup": round(float(speedup), 2),
    }
