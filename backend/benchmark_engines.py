import time
from pathlib import Path

import duckdb
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

LARGE_PRICES = DATA_DIR / "large_prices.csv"
LARGE_HOLDINGS = DATA_DIR / "large_holdings.csv"


def benchmark_pandas():
    start = time.perf_counter()

    prices = pd.read_csv(LARGE_PRICES)
    holdings = pd.read_csv(LARGE_HOLDINGS)

    merged = prices.merge(
        holdings,
        on="asset_id",
        how="inner",
    )

    merged["market_value"] = merged["close_price"] * merged["quantity"]

    result = (
        merged.groupby("date")["market_value"]
        .sum()
        .reset_index()
    )

    end = time.perf_counter()

    return len(result), end - start


def benchmark_duckdb():
    start = time.perf_counter()

    con = duckdb.connect(database=":memory:")

    result = con.execute(
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
        [str(LARGE_PRICES), str(LARGE_HOLDINGS)],
    ).fetchdf()

    end = time.perf_counter()

    return len(result), end - start


if __name__ == "__main__":
    pandas_rows, pandas_time = benchmark_pandas()
    duckdb_rows, duckdb_time = benchmark_duckdb()

    speedup = pandas_time / duckdb_time if duckdb_time > 0 else 0

    print("Large Dataset Benchmark")
    print("=======================")
    print(f"Pandas rows: {pandas_rows}")
    print(f"Pandas time: {pandas_time:.6f} seconds")
    print()
    print(f"DuckDB rows: {duckdb_rows}")
    print(f"DuckDB time: {duckdb_time:.6f} seconds")
    print()
    print(f"DuckDB speedup: {speedup:.2f}x")