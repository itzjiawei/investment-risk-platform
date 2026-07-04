from unittest.mock import Mock

import pytest

from app.services.dashboard_cache_service import clear_dashboard_cache


@pytest.fixture(autouse=True)
def reset_dashboard_cache():
    clear_dashboard_cache()
    yield
    clear_dashboard_cache()


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Investment Risk Analytics API is running",
    }


def test_get_portfolios(client, monkeypatch, portfolios_df):
    monkeypatch.setattr(
        "app.routers.market_data.load_portfolios",
        Mock(return_value=portfolios_df),
    )

    response = client.get("/api/portfolios")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0] == {
        "portfolio_id": 1,
        "portfolio_name": "Global Growth Portfolio",
    }
    assert {"portfolio_id", "portfolio_name"} <= data[0].keys()


def test_post_market_data_refresh(client, monkeypatch):
    expected_response = {
        "updated_tickers": ["AAPL"],
        "failed_tickers": [],
        "rows_inserted": 2,
        "message": "Market data refresh completed",
    }
    mocked_service = Mock(return_value=expected_response)
    monkeypatch.setattr(
        "app.routers.market_data.refresh_market_data",
        mocked_service,
    )

    response = client.post("/api/market-data/refresh")

    assert response.status_code == 200
    data = response.json()
    assert data == expected_response
    assert {
        "updated_tickers",
        "failed_tickers",
        "rows_inserted",
        "message",
    } <= data.keys()
    mocked_service.assert_called_once_with()


def test_post_market_data_refresh_with_failed_ticker(client, monkeypatch):
    expected_response = {
        "updated_tickers": ["AAPL"],
        "failed_tickers": [
            {
                "ticker": "BAD",
                "reason": "No price data returned",
            }
        ],
        "rows_inserted": 1,
        "message": "Market data refresh completed",
    }
    monkeypatch.setattr(
        "app.routers.market_data.refresh_market_data",
        Mock(return_value=expected_response),
    )

    response = client.post("/api/market-data/refresh")

    assert response.status_code == 200
    data = response.json()
    assert data["updated_tickers"] == ["AAPL"]
    assert data["failed_tickers"][0]["ticker"] == "BAD"
    assert data["failed_tickers"][0]["reason"] == "No price data returned"
    assert data["rows_inserted"] == 1


def test_post_portfolio_market_data_refresh(client, monkeypatch):
    expected_response = {
        "updated_tickers": ["AAPL"],
        "failed_tickers": [],
        "rows_inserted": 2,
        "message": "Market data refresh completed",
    }
    mocked_service = Mock(return_value=expected_response)
    monkeypatch.setattr(
        "app.routers.portfolio.refresh_market_data",
        mocked_service,
    )

    response = client.post("/api/portfolio/1/market-data/refresh")

    assert response.status_code == 200
    data = response.json()
    assert data == expected_response
    assert {
        "updated_tickers",
        "failed_tickers",
        "rows_inserted",
        "message",
    } <= data.keys()
    mocked_service.assert_called_once_with(portfolio_id=1)


def test_get_market_data_status(client, monkeypatch):
    expected_response = {
        "latest_price_date": "2026-07-03",
        "price_rows": 123,
    }
    mocked_service = Mock(return_value=expected_response)
    monkeypatch.setattr(
        "app.routers.market_data.get_market_data_status",
        mocked_service,
    )

    response = client.get("/api/market-data/status")

    assert response.status_code == 200
    data = response.json()
    assert data == expected_response
    assert {"latest_price_date", "price_rows"} <= data.keys()
    mocked_service.assert_called_once_with()


def test_get_portfolio_risk(client, monkeypatch, risk_response):
    mocked_service = Mock(return_value=risk_response)
    monkeypatch.setattr(
        "app.routers.portfolio.calculate_portfolio_risk",
        mocked_service,
    )

    response = client.get("/api/portfolio/1/risk")

    assert response.status_code == 200
    data = response.json()
    assert data == risk_response
    assert {
        "portfolio_id",
        "latest_value",
        "latest_daily_return",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "historical_var_95",
    } <= data.keys()
    mocked_service.assert_called_once_with(1)


def test_get_portfolio_dashboard(
    client,
    monkeypatch,
    risk_response,
    returns_response,
    holdings_response,
    sector_exposure_response,
    risk_contribution_response,
):
    mocked_risk = Mock(return_value=risk_response)
    mocked_returns = Mock(return_value=returns_response)
    mocked_holdings = Mock(return_value=holdings_response)
    mocked_sector_exposure = Mock(return_value=sector_exposure_response)
    mocked_risk_contribution = Mock(return_value=risk_contribution_response)

    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_risk",
        mocked_risk,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_returns",
        mocked_returns,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_holdings",
        mocked_holdings,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_sector_exposure",
        mocked_sector_exposure,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_risk_contribution",
        mocked_risk_contribution,
    )

    response = client.get("/api/portfolio/1/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "risk": risk_response,
        "returns": returns_response,
        "holdings": holdings_response,
        "sector_exposure": sector_exposure_response,
        "risk_contribution": risk_contribution_response,
    }
    assert {
        "risk",
        "returns",
        "holdings",
        "sector_exposure",
        "risk_contribution",
    } <= data.keys()
    mocked_risk.assert_called_once_with(1)
    mocked_returns.assert_called_once_with(1)
    mocked_holdings.assert_called_once_with(1)
    mocked_sector_exposure.assert_called_once_with(1)
    mocked_risk_contribution.assert_called_once_with(1)


def test_get_portfolio_dashboard_cache_hit(
    client,
    monkeypatch,
    risk_response,
    returns_response,
    holdings_response,
    sector_exposure_response,
    risk_contribution_response,
):
    mocked_risk = Mock(return_value=risk_response)
    mocked_returns = Mock(return_value=returns_response)
    mocked_holdings = Mock(return_value=holdings_response)
    mocked_sector_exposure = Mock(return_value=sector_exposure_response)
    mocked_risk_contribution = Mock(return_value=risk_contribution_response)

    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_risk",
        mocked_risk,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_returns",
        mocked_returns,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_holdings",
        mocked_holdings,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_sector_exposure",
        mocked_sector_exposure,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_risk_contribution",
        mocked_risk_contribution,
    )

    first_response = client.get("/api/portfolio/1/dashboard")
    second_response = client.get("/api/portfolio/1/dashboard")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
    mocked_risk.assert_called_once_with(1)
    mocked_returns.assert_called_once_with(1)
    mocked_holdings.assert_called_once_with(1)
    mocked_sector_exposure.assert_called_once_with(1)
    mocked_risk_contribution.assert_called_once_with(1)


def test_get_portfolio_dashboard_cache_miss_after_ttl(
    client,
    monkeypatch,
    risk_response,
    returns_response,
    holdings_response,
    sector_exposure_response,
    risk_contribution_response,
):
    current_time = {"value": 1000.0}
    mocked_risk = Mock(return_value=risk_response)

    monkeypatch.setattr(
        "app.services.dashboard_cache_service.monotonic",
        lambda: current_time["value"],
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_risk",
        mocked_risk,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_returns",
        Mock(return_value=returns_response),
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_holdings",
        Mock(return_value=holdings_response),
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_sector_exposure",
        Mock(return_value=sector_exposure_response),
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_risk_contribution",
        Mock(return_value=risk_contribution_response),
    )

    first_response = client.get("/api/portfolio/1/dashboard")
    current_time["value"] += 301
    second_response = client.get("/api/portfolio/1/dashboard")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert mocked_risk.call_count == 2


def test_portfolio_market_refresh_invalidates_dashboard_cache(
    client,
    monkeypatch,
    risk_response,
    returns_response,
    holdings_response,
    sector_exposure_response,
    risk_contribution_response,
):
    refreshed_risk_response = {
        **risk_response,
        "latest_value": risk_response["latest_value"] + 1000,
    }
    mocked_risk = Mock(side_effect=[risk_response, refreshed_risk_response])
    mocked_refresh = Mock(
        return_value={
            "updated_tickers": ["AAPL"],
            "failed_tickers": [],
            "rows_inserted": 1,
            "message": "Market data refresh completed",
        }
    )

    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_risk",
        mocked_risk,
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_returns",
        Mock(return_value=returns_response),
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_portfolio_holdings",
        Mock(return_value=holdings_response),
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_sector_exposure",
        Mock(return_value=sector_exposure_response),
    )
    monkeypatch.setattr(
        "app.services.dashboard_cache_service.calculate_risk_contribution",
        Mock(return_value=risk_contribution_response),
    )
    monkeypatch.setattr(
        "app.routers.portfolio.refresh_market_data",
        mocked_refresh,
    )

    first_dashboard = client.get("/api/portfolio/1/dashboard").json()
    refresh_response = client.post("/api/portfolio/1/market-data/refresh")
    second_dashboard = client.get("/api/portfolio/1/dashboard").json()

    assert refresh_response.status_code == 200
    assert first_dashboard["risk"]["latest_value"] == risk_response["latest_value"]
    assert (
        second_dashboard["risk"]["latest_value"]
        == refreshed_risk_response["latest_value"]
    )
    assert mocked_risk.call_count == 2
    mocked_refresh.assert_called_once_with(portfolio_id=1)


def test_get_portfolio_returns(client, monkeypatch, returns_response):
    mocked_service = Mock(return_value=returns_response)
    monkeypatch.setattr(
        "app.routers.portfolio.calculate_portfolio_returns",
        mocked_service,
    )

    response = client.get("/api/portfolio/1/returns")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == returns_response
    assert {"date", "portfolio_value", "daily_return"} <= data[0].keys()
    mocked_service.assert_called_once_with(1)


def test_get_portfolio_holdings(client, monkeypatch, holdings_response):
    mocked_service = Mock(return_value=holdings_response)
    monkeypatch.setattr(
        "app.routers.portfolio.calculate_portfolio_holdings",
        mocked_service,
    )

    response = client.get("/api/portfolio/1/holdings")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == holdings_response
    assert {
        "ticker",
        "name",
        "sector",
        "country",
        "quantity",
        "latest_price",
        "market_value",
        "weight",
    } <= data[0].keys()
    mocked_service.assert_called_once_with(1)


def test_get_sector_exposure(client, monkeypatch, sector_exposure_response):
    mocked_service = Mock(return_value=sector_exposure_response)
    monkeypatch.setattr(
        "app.routers.portfolio.calculate_sector_exposure",
        mocked_service,
    )

    response = client.get("/api/portfolio/1/sector-exposure")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == sector_exposure_response
    assert {"sector", "market_value", "weight"} <= data[0].keys()
    mocked_service.assert_called_once_with(1)


def test_get_risk_contribution(client, monkeypatch, risk_contribution_response):
    mocked_service = Mock(return_value=risk_contribution_response)
    monkeypatch.setattr(
        "app.routers.portfolio.calculate_risk_contribution",
        mocked_service,
    )

    response = client.get("/api/portfolio/1/risk-contribution")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == risk_contribution_response
    assert {
        "ticker",
        "name",
        "sector",
        "weight",
        "daily_volatility",
        "risk_score",
        "risk_contribution",
    } <= data[0].keys()
    mocked_service.assert_called_once_with(1)


def test_get_risk_report_pdf(client, monkeypatch):
    mocked_service = Mock(return_value=b"%PDF-1.4\nmock pdf")
    monkeypatch.setattr(
        "app.routers.portfolio.generate_pdf_risk_report",
        mocked_service,
    )

    response = client.get("/api/portfolio/1/risk-report/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="portfolio-1-risk-report.pdf"'
    )
    assert response.content.startswith(b"%PDF")
    mocked_service.assert_called_once_with(1)


def test_post_stress_test(client, monkeypatch, stress_test_response):
    mocked_service = Mock(return_value=stress_test_response)
    monkeypatch.setattr(
        "app.routers.portfolio.run_custom_stress_test",
        mocked_service,
    )

    payload = {
        "shocks": {
            "Technology": -20,
            "ETF": -15,
        }
    }
    response = client.post("/api/portfolio/1/stress-test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data == stress_test_response
    assert {
        "portfolio_id",
        "original_value",
        "stressed_value",
        "impact_value",
        "impact_percent",
        "breakdown",
    } <= data.keys()
    assert isinstance(data["breakdown"], list)
    assert {
        "ticker",
        "name",
        "sector",
        "market_value",
        "shock_percent",
        "estimated_loss",
        "stressed_value",
    } <= data["breakdown"][0].keys()
    mocked_service.assert_called_once_with(1, payload["shocks"])


def test_post_portfolio_compare(client, monkeypatch, comparison_response):
    mocked_service = Mock(return_value=comparison_response)
    monkeypatch.setattr(
        "app.routers.portfolio.compare_portfolios",
        mocked_service,
    )

    payload = {"portfolio_ids": [1, 2]}
    response = client.post("/api/portfolio/compare", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == comparison_response
    assert {
        "portfolio_id",
        "latest_value",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "historical_var_95",
    } <= data[0].keys()
    mocked_service.assert_called_once_with(payload["portfolio_ids"])
