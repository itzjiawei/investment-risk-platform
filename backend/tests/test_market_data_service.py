from types import SimpleNamespace

import pandas as pd

from app.services import market_data_service


class FakeTicker:
    requested_tickers = []

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.requested_tickers.append(ticker)

    def history(self, period: str, interval: str, auto_adjust: bool):
        if self.ticker in {"BAD", "BAD.SI"}:
            return pd.DataFrame()

        return pd.DataFrame(
            {
                "Close": [101.234, 102.345],
            },
            index=pd.to_datetime(["2026-07-02", "2026-07-03"]),
        )


def test_fetch_price_rows_uses_mocked_yfinance(monkeypatch):
    FakeTicker.requested_tickers = []
    fake_yfinance = SimpleNamespace(Ticker=FakeTicker)
    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: fake_yfinance,
    )

    rows = market_data_service._fetch_price_rows(
        asset_id=1,
        ticker="AAPL",
        period="5d",
    )

    assert rows == [
        {
            "asset_id": 1,
            "date": "2026-07-02",
            "close_price": 101.23,
        },
        {
            "asset_id": 1,
            "date": "2026-07-03",
            "close_price": 102.34,
        },
    ]
    assert FakeTicker.requested_tickers == ["AAPL"]


def test_refresh_market_data_uses_yfinance_ticker_mapping(monkeypatch):
    FakeTicker.requested_tickers = []
    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        lambda portfolio_id=None: [
            {
                "asset_id": 5,
                "ticker": "DBS",
                "yfinance_ticker": "D05.SI",
            },
        ],
    )

    fake_yfinance = SimpleNamespace(Ticker=FakeTicker)
    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: fake_yfinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert FakeTicker.requested_tickers == ["D05.SI"]
    assert result["updated_tickers"] == ["DBS"]
    assert result["failed_tickers"] == []
    assert result["rows_inserted"] == 2


def test_refresh_market_data_uses_known_mapping_when_column_missing(monkeypatch):
    FakeTicker.requested_tickers = []
    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        lambda portfolio_id=None: [
            {
                "asset_id": 5,
                "ticker": "DBS",
            },
        ],
    )

    fake_yfinance = SimpleNamespace(Ticker=FakeTicker)
    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: fake_yfinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert FakeTicker.requested_tickers == ["D05.SI"]
    assert result["updated_tickers"] == ["DBS"]
    assert result["failed_tickers"] == []


def test_refresh_market_data_handles_failed_ticker(monkeypatch):
    FakeTicker.requested_tickers = []
    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        lambda portfolio_id=None: [
            {"asset_id": 1, "ticker": "AAPL"},
            {
                "asset_id": 2,
                "ticker": "BAD",
                "yfinance_ticker": "BAD.SI",
            },
        ],
    )

    fake_yfinance = SimpleNamespace(Ticker=FakeTicker)
    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: fake_yfinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert FakeTicker.requested_tickers == ["AAPL", "BAD.SI"]
    assert result == {
        "updated_tickers": ["AAPL"],
        "failed_tickers": [
            {
                "ticker": "BAD",
                "yfinance_ticker": "BAD.SI",
                "reason": "No price data returned",
            }
        ],
        "rows_inserted": 2,
        "message": "Market data refresh completed",
    }


def test_refresh_market_data_filters_by_portfolio(monkeypatch):
    FakeTicker.requested_tickers = []
    requested_portfolio_ids = []

    def fake_get_relevant_assets(portfolio_id=None):
        requested_portfolio_ids.append(portfolio_id)
        return [{"asset_id": 1, "ticker": "AAPL"}]

    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        fake_get_relevant_assets,
    )

    fake_yfinance = SimpleNamespace(Ticker=FakeTicker)
    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: fake_yfinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(
        period="5d",
        portfolio_id=7,
    )

    assert requested_portfolio_ids == [7]
    assert result["updated_tickers"] == ["AAPL"]
    assert result["rows_inserted"] == 2
