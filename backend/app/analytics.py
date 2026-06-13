from app.data_loader import load_holdings, load_prices, load_assets
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import time

def calculate_portfolio_value(portfolio_id: int):
    holdings = load_holdings()
    prices = load_prices()
    assets = load_assets()

    portfolio_holdings = holdings[holdings["portfolio_id"] == portfolio_id]

    if portfolio_holdings.empty:
        return []

    merged = prices.merge(
        portfolio_holdings,
        on="asset_id",
        how="inner"
    )

    merged["market_value"] = merged["close_price"] * merged["quantity"]

    portfolio_value = (
        merged
        .groupby("date")["market_value"]
        .sum()
        .reset_index()
    )

    portfolio_value = portfolio_value.rename(
        columns={"market_value": "portfolio_value"}
    )

    portfolio_value["portfolio_value"] = portfolio_value["portfolio_value"].round(2)

    return portfolio_value.to_dict(orient="records")

def calculate_portfolio_risk(portfolio_id: int):
    portfolio_values = calculate_portfolio_value(portfolio_id)

    if not portfolio_values:
        return {"error": "Portfolio not found or has no data"}

    df = pd.DataFrame(portfolio_values)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    df["daily_return"] = df["portfolio_value"].pct_change()

    returns = df["daily_return"].dropna()

    if returns.empty:
        return {"error": "Not enough data to calculate risk metrics"}

    latest_value = df["portfolio_value"].iloc[-1]
    latest_daily_return = returns.iloc[-1]

    average_daily_return = returns.mean()
    daily_volatility = returns.std()

    trading_days = 252

    annualized_return = average_daily_return * trading_days
    annualized_volatility = daily_volatility * np.sqrt(trading_days)

    risk_free_rate = 0.02

    sharpe_ratio = (
        (annualized_return - risk_free_rate) / annualized_volatility
        if annualized_volatility != 0
        else 0
    )

    df["running_max"] = df["portfolio_value"].cummax()
    df["drawdown"] = (
        df["portfolio_value"] - df["running_max"]
    ) / df["running_max"]

    max_drawdown = df["drawdown"].min()

    historical_var_95 = np.percentile(returns, 5)

    return {
        "portfolio_id": portfolio_id,
        "latest_value": round(float(latest_value), 2),
        "latest_daily_return": round(float(latest_daily_return), 6),
        "annualized_return": round(float(annualized_return), 6),
        "annualized_volatility": round(float(annualized_volatility), 6),
        "sharpe_ratio": round(float(sharpe_ratio), 4),
        "max_drawdown": round(float(max_drawdown), 6),
        "historical_var_95": round(float(historical_var_95), 6),
    }

def calculate_portfolio_returns(portfolio_id: int):
    portfolio_values = calculate_portfolio_value(portfolio_id)

    if not portfolio_values:
        return []

    df = pd.DataFrame(portfolio_values)

    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values("date")

    df["daily_return"] = (
        df["portfolio_value"]
        .pct_change()
    )

    df["daily_return"] = (
        df["daily_return"]
        .fillna(0)
        .round(6)
    )

    df["portfolio_value"] = (
        df["portfolio_value"]
        .round(2)
    )

    return df.to_dict(orient="records")

def calculate_portfolio_holdings(portfolio_id: int):
    holdings = load_holdings()
    prices = load_prices()
    assets = load_assets()

    portfolio_holdings = holdings[holdings["portfolio_id"] == portfolio_id]

    if portfolio_holdings.empty:
        return []

    prices["date"] = pd.to_datetime(prices["date"])

    latest_date = prices["date"].max()

    latest_prices = prices[prices["date"] == latest_date]

    merged = (
        portfolio_holdings
        .merge(assets, on="asset_id", how="left")
        .merge(latest_prices, on="asset_id", how="left")
    )

    merged["market_value"] = merged["quantity"] * merged["close_price"]

    total_value = merged["market_value"].sum()

    merged["weight"] = merged["market_value"] / total_value

    result = merged[[
        "ticker",
        "name",
        "sector",
        "country",
        "quantity",
        "close_price",
        "market_value",
        "weight",
    ]].copy()

    result = result.rename(columns={
        "close_price": "latest_price"
    })

    result["latest_price"] = result["latest_price"].round(2)
    result["market_value"] = result["market_value"].round(2)
    result["weight"] = result["weight"].round(6)

    return result.to_dict(orient="records")

def calculate_sector_exposure(portfolio_id: int):
    holdings_data = calculate_portfolio_holdings(portfolio_id)

    if not holdings_data:
        return []

    df = pd.DataFrame(holdings_data)

    sector_exposure = (
        df.groupby("sector")["market_value"]
        .sum()
        .reset_index()
    )

    total_value = sector_exposure["market_value"].sum()

    sector_exposure["weight"] = (
        sector_exposure["market_value"] / total_value
    )

    sector_exposure["market_value"] = sector_exposure["market_value"].round(2)
    sector_exposure["weight"] = sector_exposure["weight"].round(6)

    return sector_exposure.to_dict(orient="records")

def calculate_risk_contribution(portfolio_id: int):
    holdings_data = calculate_portfolio_holdings(portfolio_id)

    if not holdings_data:
        return []

    holdings_df = pd.DataFrame(holdings_data)
    prices = load_prices()
    assets = load_assets()

    prices["date"] = pd.to_datetime(prices["date"])
    prices = prices.sort_values(["asset_id", "date"])

    prices["daily_return"] = (
        prices.groupby("asset_id")["close_price"]
        .pct_change()
    )

    asset_volatility = (
        prices.groupby("asset_id")["daily_return"]
        .std()
        .reset_index()
    )

    asset_volatility = asset_volatility.rename(
        columns={"daily_return": "daily_volatility"}
    )

    merged = (
        holdings_df
        .merge(assets[["asset_id", "ticker"]], on="ticker", how="left")
        .merge(asset_volatility, on="asset_id", how="left")
    )

    merged["risk_score"] = (
        merged["weight"] * merged["daily_volatility"]
    )

    total_risk_score = merged["risk_score"].sum()

    if total_risk_score == 0:
        merged["risk_contribution"] = 0
    else:
        merged["risk_contribution"] = (
            merged["risk_score"] / total_risk_score
        )

    result = merged[[
        "ticker",
        "name",
        "sector",
        "weight",
        "daily_volatility",
        "risk_score",
        "risk_contribution",
    ]].copy()

    result["weight"] = result["weight"].round(6)
    result["daily_volatility"] = result["daily_volatility"].round(6)
    result["risk_score"] = result["risk_score"].round(6)
    result["risk_contribution"] = result["risk_contribution"].round(6)

    result = result.sort_values(
        "risk_contribution",
        ascending=False
    )

    return result.to_dict(orient="records")

def run_custom_stress_test(portfolio_id: int, shocks: dict):
    holdings_data = calculate_portfolio_holdings(portfolio_id)

    if not holdings_data:
        return {"error": "Portfolio not found or has no holdings"}

    df = pd.DataFrame(holdings_data)

    df["shock_percent"] = df["sector"].map(shocks).fillna(0)

    df["shock_decimal"] = df["shock_percent"] / 100

    df["estimated_loss"] = df["market_value"] * df["shock_decimal"]

    total_value = df["market_value"].sum()
    total_impact = df["estimated_loss"].sum()

    stressed_value = total_value + total_impact

    df["stressed_value"] = df["market_value"] + df["estimated_loss"]

    breakdown = df[[
        "ticker",
        "name",
        "sector",
        "market_value",
        "shock_percent",
        "estimated_loss",
        "stressed_value",
    ]].copy()

    breakdown["market_value"] = breakdown["market_value"].round(2)
    breakdown["estimated_loss"] = breakdown["estimated_loss"].round(2)
    breakdown["stressed_value"] = breakdown["stressed_value"].round(2)

    return {
        "portfolio_id": portfolio_id,
        "original_value": round(float(total_value), 2),
        "stressed_value": round(float(stressed_value), 2),
        "impact_value": round(float(total_impact), 2),
        "impact_percent": round(float(total_impact / total_value), 6),
        "breakdown": breakdown.to_dict(orient="records"),
    }

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

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

def run_large_dataset_benchmark():
    large_prices = DATA_DIR / "large_prices.csv"
    large_holdings = DATA_DIR / "large_holdings.csv"

    # Pandas benchmark
    start = time.perf_counter()

    prices = pd.read_csv(large_prices)
    holdings = pd.read_csv(large_holdings)

    merged = prices.merge(
        holdings,
        on="asset_id",
        how="inner",
    )

    merged["market_value"] = merged["close_price"] * merged["quantity"]

    pandas_result = (
        merged.groupby("date")["market_value"]
        .sum()
        .reset_index()
    )

    pandas_time = time.perf_counter() - start

    # DuckDB benchmark
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