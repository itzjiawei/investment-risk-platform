from types import SimpleNamespace
from unittest.mock import Mock

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


def _fake_download_frame(tickers: list[str]):
    index = pd.to_datetime(["2026-07-02", "2026-07-03"])

    if len(tickers) == 1:
        ticker = tickers[0]
        close_values = [None, None] if ticker in {"BAD", "BAD.SI"} else [101.234, 102.345]
        return pd.DataFrame({"Close": close_values}, index=index)

    data = {}
    for ticker in tickers:
        close_values = [None, None] if ticker in {"BAD", "BAD.SI"} else [101.234, 102.345]
        data[(ticker, "Close")] = close_values

    return pd.DataFrame(
        data,
        index=index,
        columns=pd.MultiIndex.from_tuples(data.keys()),
    )


class FakeYFinance:
    requested_downloads = []
    Ticker = FakeTicker

    @classmethod
    def download(cls, tickers: str, **kwargs):
        requested_tickers = tickers.split()
        cls.requested_downloads.append(
            {
                "tickers": requested_tickers,
                "kwargs": kwargs,
            }
        )
        return _fake_download_frame(requested_tickers)


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
    FakeYFinance.requested_downloads = []
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

    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: FakeYFinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert FakeYFinance.requested_downloads[0]["tickers"] == ["D05.SI"]
    assert result["updated_tickers"] == ["DBS"]
    assert result["failed_tickers"] == []
    assert result["rows_inserted"] == 2


def test_refresh_market_data_uses_known_mapping_when_column_missing(monkeypatch):
    FakeYFinance.requested_downloads = []
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

    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: FakeYFinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert FakeYFinance.requested_downloads[0]["tickers"] == ["D05.SI"]
    assert result["updated_tickers"] == ["DBS"]
    assert result["failed_tickers"] == []


def test_refresh_market_data_handles_failed_ticker(monkeypatch):
    FakeYFinance.requested_downloads = []
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

    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: FakeYFinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert FakeYFinance.requested_downloads[0]["tickers"] == ["AAPL", "BAD.SI"]
    assert result == {
        "updated_tickers": ["AAPL"],
        "failed_tickers": [
            {
                "ticker": "BAD",
                "yfinance_ticker": "BAD.SI",
                "reason": "No price data returned from yfinance",
                "category": "empty_response",
                "period": "5d",
                "interval": "1d",
                "source": "individual_fallback",
            }
        ],
        "rows_inserted": 2,
        "message": "Market data refresh completed",
    }


def test_refresh_market_data_filters_by_portfolio(monkeypatch):
    FakeYFinance.requested_downloads = []
    requested_portfolio_ids = []

    def fake_get_relevant_assets(portfolio_id=None):
        requested_portfolio_ids.append(portfolio_id)
        return [{"asset_id": 1, "ticker": "AAPL"}]

    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        fake_get_relevant_assets,
    )

    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: FakeYFinance,
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


def test_refresh_market_data_deduplicates_yfinance_downloads(monkeypatch):
    FakeYFinance.requested_downloads = []
    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        lambda portfolio_id=None: [
            {"asset_id": 1, "ticker": "AAPL"},
            {"asset_id": 2, "ticker": "APPLE FUND", "yfinance_ticker": "AAPL"},
        ],
    )
    monkeypatch.setattr(
        market_data_service,
        "_get_yfinance_module",
        lambda: FakeYFinance,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert FakeYFinance.requested_downloads == [
        {
            "tickers": ["AAPL"],
            "kwargs": {
                "period": "5d",
                "interval": "1d",
                "auto_adjust": False,
                "group_by": "ticker",
                "threads": False,
                "progress": False,
            },
        }
    ]
    assert result["updated_tickers"] == ["AAPL", "APPLE FUND"]
    assert result["rows_inserted"] == 4


def test_market_data_batch_download_retries_after_rate_limit(monkeypatch):
    attempts = {"count": 0}
    sleep_mock = Mock()

    def flaky_download(tickers, period):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise Exception("Too Many Requests. Rate Limited. Try after a while.")

        return _fake_download_frame(tickers)

    monkeypatch.setattr(market_data_service, "_download_tickers", flaky_download)
    monkeypatch.setattr(market_data_service, "_sleep", sleep_mock)

    histories, failures, sources = market_data_service._download_ticker_histories(
        ["AAPL"],
        "5d",
    )

    assert failures == {}
    assert "AAPL" in histories
    assert sources["AAPL"] == "batch"
    assert attempts["count"] == 2
    sleep_mock.assert_called_once()


def test_refresh_market_data_uses_individual_fallback_when_batch_is_empty(
    monkeypatch,
):
    fallback_download = Mock(
        return_value=pd.DataFrame(
            {"Close": [500.00]},
            index=pd.to_datetime(["2026-07-03"]),
        )
    )

    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        lambda portfolio_id=None: [{"asset_id": 1, "ticker": "SPY"}],
    )
    monkeypatch.setattr(
        market_data_service,
        "_download_tickers",
        lambda tickers, period: pd.DataFrame(
            {"Close": [None]},
            index=pd.to_datetime(["2026-07-03"]),
        ),
    )
    monkeypatch.setattr(
        market_data_service,
        "_download_ticker_history",
        fallback_download,
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        lambda asset_id, price_rows: len(price_rows),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert result["updated_tickers"] == ["SPY"]
    assert result["failed_tickers"] == []
    assert result["rows_inserted"] == 1
    fallback_download.assert_called_once_with("SPY", "5d")


def test_refresh_market_data_reports_empty_response_diagnostics(monkeypatch):
    monkeypatch.setattr(
        market_data_service,
        "_get_relevant_assets",
        lambda portfolio_id=None: [{"asset_id": 1, "ticker": "SPY"}],
    )
    monkeypatch.setattr(
        market_data_service,
        "_download_tickers",
        lambda tickers, period: pd.DataFrame(
            {"Close": [None]},
            index=pd.to_datetime(["2026-07-03"]),
        ),
    )
    monkeypatch.setattr(
        market_data_service,
        "_download_ticker_history",
        lambda ticker, period: pd.DataFrame(
            {"Close": [None]},
            index=pd.to_datetime(["2026-07-03"]),
        ),
    )
    monkeypatch.setattr(
        market_data_service,
        "_insert_new_price_rows",
        Mock(side_effect=AssertionError("null rows should not be inserted")),
    )

    result = market_data_service.refresh_market_data(period="5d")

    assert result["updated_tickers"] == []
    assert result["rows_inserted"] == 0
    assert result["failed_tickers"] == [
        {
            "ticker": "SPY",
            "yfinance_ticker": "SPY",
            "reason": "No price data returned from yfinance",
            "category": "empty_response",
            "period": "5d",
            "interval": "1d",
            "source": "individual_fallback",
        }
    ]
