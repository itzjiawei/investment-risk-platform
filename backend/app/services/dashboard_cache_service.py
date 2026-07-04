from copy import deepcopy
from time import monotonic
from typing import Any

from app.services.portfolio_service import (
    calculate_portfolio_holdings,
    calculate_portfolio_returns,
    calculate_portfolio_risk,
    calculate_risk_contribution,
    calculate_sector_exposure,
)


DASHBOARD_CACHE_TTL_SECONDS = 300

_dashboard_cache: dict[int, tuple[float, dict[str, Any]]] = {}


def get_portfolio_dashboard_data(portfolio_id: int) -> dict[str, Any]:
    now = monotonic()
    cached_entry = _dashboard_cache.get(portfolio_id)

    if cached_entry is not None:
        cached_at, cached_data = cached_entry

        if now - cached_at < DASHBOARD_CACHE_TTL_SECONDS:
            return deepcopy(cached_data)

    dashboard_data = _build_portfolio_dashboard_data(portfolio_id)
    _dashboard_cache[portfolio_id] = (now, dashboard_data)
    return deepcopy(dashboard_data)


def invalidate_portfolio_dashboard_cache(portfolio_id: int) -> None:
    _dashboard_cache.pop(portfolio_id, None)


def invalidate_all_dashboard_cache() -> None:
    _dashboard_cache.clear()


def clear_dashboard_cache() -> None:
    _dashboard_cache.clear()


def _build_portfolio_dashboard_data(portfolio_id: int) -> dict[str, Any]:
    return {
        "risk": calculate_portfolio_risk(portfolio_id),
        "returns": calculate_portfolio_returns(portfolio_id),
        "holdings": calculate_portfolio_holdings(portfolio_id),
        "sector_exposure": calculate_sector_exposure(portfolio_id),
        "risk_contribution": calculate_risk_contribution(portfolio_id),
    }
