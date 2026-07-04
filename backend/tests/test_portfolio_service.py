import math

import pandas as pd

from app.services import portfolio_service


def _assert_json_safe(value):
    if isinstance(value, dict):
        for child in value.values():
            _assert_json_safe(child)
        return

    if isinstance(value, list):
        for child in value:
            _assert_json_safe(child)
        return

    if isinstance(value, float):
        assert math.isfinite(value)


def test_sector_exposure_normal_case(monkeypatch):
    assets = pd.DataFrame(
        [
            {
                "asset_id": 1,
                "ticker": "AAPL",
                "name": "Apple",
                "sector": "Technology",
                "country": "US",
            },
            {
                "asset_id": 2,
                "ticker": "SPY",
                "name": "S&P 500 ETF",
                "sector": "ETF",
                "country": "US",
            },
        ]
    )
    holdings = pd.DataFrame(
        [
            {"portfolio_id": 1, "asset_id": 1, "quantity": 10},
            {"portfolio_id": 1, "asset_id": 2, "quantity": 20},
        ]
    )
    prices = pd.DataFrame(
        [
            {"asset_id": 1, "date": "2026-07-03", "close_price": 200.0},
            {"asset_id": 2, "date": "2026-07-03", "close_price": 50.0},
        ]
    )

    monkeypatch.setattr(portfolio_service, "load_assets", lambda: assets)
    monkeypatch.setattr(portfolio_service, "load_holdings", lambda: holdings)
    monkeypatch.setattr(portfolio_service, "load_prices", lambda: prices)

    result = portfolio_service.calculate_sector_exposure(1)

    assert result == [
        {
            "sector": "ETF",
            "market_value": 1000.0,
            "weight": 0.333333,
        },
        {
            "sector": "Technology",
            "market_value": 2000.0,
            "weight": 0.666667,
        },
    ]
    _assert_json_safe(result)


def test_holdings_use_latest_valid_price_per_asset(monkeypatch):
    assets = pd.DataFrame(
        [
            {
                "asset_id": 1,
                "ticker": "AAPL",
                "name": "Apple",
                "sector": "Technology",
                "country": "US",
            },
            {
                "asset_id": 2,
                "ticker": "DBS",
                "name": "DBS Bank",
                "sector": "Financials",
                "country": "Singapore",
            },
        ]
    )
    holdings = pd.DataFrame(
        [
            {"portfolio_id": 1, "asset_id": 1, "quantity": 10},
            {"portfolio_id": 1, "asset_id": 2, "quantity": 20},
        ]
    )
    prices = pd.DataFrame(
        [
            {"asset_id": 1, "date": "2026-07-03", "close_price": 200.0},
            {"asset_id": 2, "date": "2026-07-02", "close_price": 40.0},
        ]
    )

    monkeypatch.setattr(portfolio_service, "load_assets", lambda: assets)
    monkeypatch.setattr(portfolio_service, "load_holdings", lambda: holdings)
    monkeypatch.setattr(portfolio_service, "load_prices", lambda: prices)

    result = portfolio_service.calculate_portfolio_holdings(1)

    assert result == [
        {
            "ticker": "AAPL",
            "name": "Apple",
            "sector": "Technology",
            "country": "US",
            "quantity": 10,
            "latest_price": 200.0,
            "market_value": 2000.0,
            "weight": 0.714286,
        },
        {
            "ticker": "DBS",
            "name": "DBS Bank",
            "sector": "Financials",
            "country": "Singapore",
            "quantity": 20,
            "latest_price": 40.0,
            "market_value": 800.0,
            "weight": 0.285714,
        }
    ]
    _assert_json_safe(result)


def test_sector_exposure_uses_latest_valid_price_per_asset(monkeypatch):
    assets = pd.DataFrame(
        [
            {
                "asset_id": 1,
                "ticker": "AAPL",
                "name": "Apple",
                "sector": "Technology",
                "country": "US",
            },
            {
                "asset_id": 2,
                "ticker": "DBS",
                "name": "DBS Bank",
                "sector": "Financials",
                "country": "Singapore",
            },
        ]
    )
    holdings = pd.DataFrame(
        [
            {"portfolio_id": 1, "asset_id": 1, "quantity": 10},
            {"portfolio_id": 1, "asset_id": 2, "quantity": 20},
        ]
    )
    prices = pd.DataFrame(
        [
            {"asset_id": 1, "date": "2026-07-03", "close_price": 200.0},
            {"asset_id": 2, "date": "2026-07-02", "close_price": 40.0},
        ]
    )

    monkeypatch.setattr(portfolio_service, "load_assets", lambda: assets)
    monkeypatch.setattr(portfolio_service, "load_holdings", lambda: holdings)
    monkeypatch.setattr(portfolio_service, "load_prices", lambda: prices)

    result = portfolio_service.calculate_sector_exposure(1)

    assert result == [
        {
            "sector": "Financials",
            "market_value": 800.0,
            "weight": 0.285714,
        },
        {
            "sector": "Technology",
            "market_value": 2000.0,
            "weight": 0.714286,
        }
    ]
    _assert_json_safe(result)


def test_sector_exposure_skips_ticker_with_no_valid_price(monkeypatch):
    assets = pd.DataFrame(
        [
            {
                "asset_id": 1,
                "ticker": "AAPL",
                "name": "Apple",
                "sector": "Technology",
                "country": "US",
            },
            {
                "asset_id": 2,
                "ticker": "DBS",
                "name": "DBS Bank",
                "sector": "Financials",
                "country": "Singapore",
            },
        ]
    )
    holdings = pd.DataFrame(
        [
            {"portfolio_id": 1, "asset_id": 1, "quantity": 10},
            {"portfolio_id": 1, "asset_id": 2, "quantity": 20},
        ]
    )
    prices = pd.DataFrame(
        [
            {"asset_id": 1, "date": "2026-07-03", "close_price": 200.0},
        ]
    )

    monkeypatch.setattr(portfolio_service, "load_assets", lambda: assets)
    monkeypatch.setattr(portfolio_service, "load_holdings", lambda: holdings)
    monkeypatch.setattr(portfolio_service, "load_prices", lambda: prices)

    result = portfolio_service.calculate_sector_exposure(1)

    assert result == [
        {
            "sector": "Technology",
            "market_value": 2000.0,
            "weight": 1.0,
        }
    ]
    _assert_json_safe(result)


def test_sector_exposure_returns_empty_when_total_market_value_is_zero(monkeypatch):
    assets = pd.DataFrame(
        [
            {
                "asset_id": 1,
                "ticker": "AAPL",
                "name": "Apple",
                "sector": "Technology",
                "country": "US",
            },
        ]
    )
    holdings = pd.DataFrame(
        [
            {"portfolio_id": 1, "asset_id": 1, "quantity": 10},
        ]
    )
    prices = pd.DataFrame(
        [
            {"asset_id": 1, "date": "2026-07-03", "close_price": 0.0},
        ]
    )

    monkeypatch.setattr(portfolio_service, "load_assets", lambda: assets)
    monkeypatch.setattr(portfolio_service, "load_holdings", lambda: holdings)
    monkeypatch.setattr(portfolio_service, "load_prices", lambda: prices)

    assert portfolio_service.calculate_portfolio_holdings(1) == []
    assert portfolio_service.calculate_sector_exposure(1) == []


def test_sector_exposure_prevents_nan_values(monkeypatch):
    assets = pd.DataFrame(
        [
            {
                "asset_id": 1,
                "ticker": "AAPL",
                "name": "Apple",
                "sector": "Technology",
                "country": "US",
            },
            {
                "asset_id": 2,
                "ticker": "DBS",
                "name": "DBS Bank",
                "sector": "Financials",
                "country": "Singapore",
            },
        ]
    )
    holdings = pd.DataFrame(
        [
            {"portfolio_id": 1, "asset_id": 1, "quantity": 10},
            {"portfolio_id": 1, "asset_id": 2, "quantity": 20},
        ]
    )
    prices = pd.DataFrame(
        [
            {"asset_id": 1, "date": "2026-07-03", "close_price": float("nan")},
            {"asset_id": 2, "date": "2026-07-03", "close_price": float("inf")},
        ]
    )

    monkeypatch.setattr(portfolio_service, "load_assets", lambda: assets)
    monkeypatch.setattr(portfolio_service, "load_holdings", lambda: holdings)
    monkeypatch.setattr(portfolio_service, "load_prices", lambda: prices)

    result = portfolio_service.calculate_sector_exposure(1)

    assert result == []
    _assert_json_safe(result)
