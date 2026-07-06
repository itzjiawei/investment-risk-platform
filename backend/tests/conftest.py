import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.services.auth_service import get_current_user


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 1,
        "email": "demo@example.com",
        "full_name": "Demo User",
        "role": "admin",
        "is_active": True,
    }

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def portfolios_df():
    return pd.DataFrame(
        [
            {"portfolio_id": 1, "portfolio_name": "Global Growth Portfolio"},
            {"portfolio_id": 2, "portfolio_name": "Asia Balanced Portfolio"},
        ]
    )


@pytest.fixture
def risk_response():
    return {
        "portfolio_id": 1,
        "latest_value": 157500.25,
        "latest_daily_return": 0.0025,
        "annualized_return": 0.1123,
        "annualized_volatility": 0.1845,
        "sharpe_ratio": 0.5,
        "max_drawdown": -0.12,
        "historical_var_95": -0.021,
    }


@pytest.fixture
def returns_response():
    return [
        {
            "date": "2025-01-01",
            "portfolio_value": 100000.0,
            "daily_return": 0.0,
        },
        {
            "date": "2025-01-02",
            "portfolio_value": 101250.5,
            "daily_return": 0.012505,
        },
    ]


@pytest.fixture
def holdings_response():
    return [
        {
            "ticker": "AAPL",
            "name": "Apple",
            "sector": "Technology",
            "country": "US",
            "quantity": 100,
            "latest_price": 185.25,
            "market_value": 18525.0,
            "weight": 0.25,
        }
    ]


@pytest.fixture
def sector_exposure_response():
    return [
        {
            "sector": "Technology",
            "market_value": 85000.0,
            "weight": 0.54,
        },
        {
            "sector": "ETF",
            "market_value": 72500.25,
            "weight": 0.46,
        },
    ]


@pytest.fixture
def risk_contribution_response():
    return [
        {
            "ticker": "AAPL",
            "name": "Apple",
            "sector": "Technology",
            "weight": 0.25,
            "daily_volatility": 0.018,
            "risk_score": 0.0045,
            "risk_contribution": 0.31,
        }
    ]


@pytest.fixture
def stress_test_response():
    return {
        "portfolio_id": 1,
        "original_value": 157500.25,
        "stressed_value": 132400.0,
        "impact_value": -25100.25,
        "impact_percent": -0.159366,
        "breakdown": [
            {
                "ticker": "AAPL",
                "name": "Apple",
                "sector": "Technology",
                "market_value": 18525.0,
                "shock_percent": -20,
                "estimated_loss": -3705.0,
                "stressed_value": 14820.0,
            }
        ],
    }


@pytest.fixture
def comparison_response():
    return [
        {
            "portfolio_id": 1,
            "latest_value": 157500.25,
            "annualized_return": 0.1123,
            "annualized_volatility": 0.1845,
            "sharpe_ratio": 0.5,
            "max_drawdown": -0.12,
            "historical_var_95": -0.021,
        },
        {
            "portfolio_id": 2,
            "latest_value": 122100.0,
            "annualized_return": 0.083,
            "annualized_volatility": 0.142,
            "sharpe_ratio": 0.44,
            "max_drawdown": -0.09,
            "historical_var_95": -0.018,
        },
    ]
