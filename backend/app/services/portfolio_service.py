import numpy as np
import pandas as pd

from app.database.repository import load_assets, load_holdings, load_prices


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
