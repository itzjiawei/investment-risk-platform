import logging

import numpy as np
import pandas as pd

from app.database.repository import load_assets, load_holdings, load_prices


logger = logging.getLogger(__name__)


def calculate_portfolio_value(portfolio_id: int):
    holdings = load_holdings()
    prices = load_prices()

    portfolio_holdings = holdings[holdings["portfolio_id"] == portfolio_id]

    if portfolio_holdings.empty:
        return []

    merged = prices.merge(
        portfolio_holdings,
        on="asset_id",
        how="inner",
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
    merged = _build_latest_holdings_frame(portfolio_id)

    if merged.empty:
        return []

    total_holdings_count = len(merged)
    missing_price_tickers = _get_missing_price_tickers(merged)

    priced_holdings = _filter_priced_holdings(merged)

    logger.info(
        "Portfolio holdings calculated for portfolio_id=%s holdings_count=%s missing_price_tickers=%s priced_holdings_count=%s",
        portfolio_id,
        total_holdings_count,
        missing_price_tickers,
        len(priced_holdings),
    )

    if priced_holdings.empty:
        return []

    total_value = priced_holdings["market_value"].sum()

    if not _is_valid_positive_number(total_value):
        return []

    priced_holdings["weight"] = priced_holdings["market_value"] / total_value
    priced_holdings["weight"] = _clean_numeric_series(priced_holdings["weight"])

    result = priced_holdings[[
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

    return _to_json_safe_records(result)


def calculate_sector_exposure(portfolio_id: int):
    merged = _build_latest_holdings_frame(portfolio_id)

    if merged.empty:
        logger.info(
            "Sector exposure empty for portfolio_id=%s holdings_count=0 missing_price_tickers=[] output_count=0",
            portfolio_id,
        )
        return []

    holdings_count = len(merged)
    missing_price_tickers = _get_missing_price_tickers(merged)
    priced_holdings = _filter_priced_holdings(merged)

    if priced_holdings.empty:
        logger.info(
            "Sector exposure empty for portfolio_id=%s holdings_count=%s missing_price_tickers=%s output_count=0",
            portfolio_id,
            holdings_count,
            missing_price_tickers,
        )
        return []

    total_holdings_value = priced_holdings["market_value"].sum()

    if not _is_valid_positive_number(total_holdings_value):
        logger.info(
            "Sector exposure empty for portfolio_id=%s holdings_count=%s missing_price_tickers=%s total_market_value=%s output_count=0",
            portfolio_id,
            holdings_count,
            missing_price_tickers,
            total_holdings_value,
        )
        return []

    sector_exposure = (
        priced_holdings.groupby("sector")["market_value"]
        .sum()
        .reset_index()
    )

    sector_exposure["market_value"] = _clean_numeric_series(
        sector_exposure["market_value"]
    )
    sector_exposure = sector_exposure.dropna(subset=["market_value"])

    total_value = sector_exposure["market_value"].sum()

    if not _is_valid_positive_number(total_value):
        logger.info(
            "Sector exposure empty for portfolio_id=%s holdings_count=%s missing_price_tickers=%s total_market_value=%s output_count=0",
            portfolio_id,
            holdings_count,
            missing_price_tickers,
            total_value,
        )
        return []

    sector_exposure["weight"] = (
        sector_exposure["market_value"] / total_value
    )

    sector_exposure["market_value"] = sector_exposure["market_value"].round(2)
    sector_exposure["weight"] = sector_exposure["weight"].round(6)

    records = _to_json_safe_records(sector_exposure)
    logger.info(
        "Sector exposure calculated for portfolio_id=%s holdings_count=%s missing_price_tickers=%s output_count=%s",
        portfolio_id,
        holdings_count,
        missing_price_tickers,
        len(records),
    )
    return records


def _build_latest_holdings_frame(portfolio_id: int) -> pd.DataFrame:
    holdings = load_holdings()
    prices = load_prices()
    assets = load_assets()

    portfolio_holdings = holdings[holdings["portfolio_id"] == portfolio_id]

    if portfolio_holdings.empty or prices.empty:
        return pd.DataFrame()

    prices["date"] = pd.to_datetime(prices["date"], errors="coerce")
    prices["close_price"] = _clean_numeric_series(prices["close_price"])

    valid_prices = prices.dropna(subset=["asset_id", "date", "close_price"]).copy()

    if valid_prices.empty:
        return pd.DataFrame()

    latest_prices = (
        valid_prices
        .sort_values(["asset_id", "date"])
        .groupby("asset_id", as_index=False)
        .tail(1)
    )

    return (
        portfolio_holdings
        .merge(assets, on="asset_id", how="left")
        .merge(latest_prices, on="asset_id", how="left")
    )


def _filter_priced_holdings(holdings: pd.DataFrame) -> pd.DataFrame:
    priced_holdings = holdings.copy()
    priced_holdings["quantity"] = _clean_numeric_series(priced_holdings["quantity"])
    priced_holdings["close_price"] = _clean_numeric_series(
        priced_holdings["close_price"]
    )
    priced_holdings = priced_holdings.dropna(
        subset=["quantity", "close_price"],
    ).copy()

    if priced_holdings.empty:
        return priced_holdings

    priced_holdings["market_value"] = (
        priced_holdings["quantity"] * priced_holdings["close_price"]
    )
    priced_holdings["market_value"] = _clean_numeric_series(
        priced_holdings["market_value"]
    )
    return priced_holdings.dropna(subset=["market_value"]).copy()


def _get_missing_price_tickers(holdings: pd.DataFrame) -> list[str]:
    if holdings.empty or "close_price" not in holdings.columns:
        return []

    close_prices = _clean_numeric_series(holdings["close_price"])
    tickers = holdings.loc[
        close_prices.isna(),
        "ticker",
    ].dropna()
    return sorted(
        str(ticker)
        for ticker in tickers.unique()
    )


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
    merged["risk_score"] = _clean_numeric_series(merged["risk_score"]).fillna(0)

    total_risk_score = merged["risk_score"].sum()

    if not _is_valid_positive_number(total_risk_score):
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
    result["daily_volatility"] = result["daily_volatility"].fillna(0).round(6)
    result["risk_score"] = result["risk_score"].round(6)
    result["risk_contribution"] = result["risk_contribution"].round(6)

    result = result.sort_values(
        "risk_contribution",
        ascending=False
    )

    return _to_json_safe_records(result)


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

    if not _is_valid_positive_number(total_value):
        return {"error": "Portfolio has no priced holdings"}

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
        "breakdown": _to_json_safe_records(breakdown),
    }


def compare_portfolios(portfolio_ids: list[int]):
    comparison = []

    for portfolio_id in portfolio_ids:
        risk = calculate_portfolio_risk(portfolio_id)

        if "error" in risk:
            continue

        comparison.append({
            "portfolio_id": portfolio_id,
            "latest_value": risk["latest_value"],
            "annualized_return": risk["annualized_return"],
            "annualized_volatility": risk["annualized_volatility"],
            "sharpe_ratio": risk["sharpe_ratio"],
            "max_drawdown": risk["max_drawdown"],
            "historical_var_95": risk["historical_var_95"],
        })

    return comparison


def _clean_numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace(
        [np.inf, -np.inf],
        np.nan,
    )


def _is_valid_positive_number(value) -> bool:
    return pd.notna(value) and np.isfinite(float(value)) and float(value) > 0


def _to_json_safe_records(df: pd.DataFrame):
    safe_df = df.replace([np.inf, -np.inf], np.nan)
    safe_df = safe_df.astype(object).where(pd.notna(safe_df), None)
    return safe_df.to_dict(orient="records")
