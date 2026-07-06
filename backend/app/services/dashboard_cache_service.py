from copy import deepcopy
import logging
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
logger = logging.getLogger(__name__)

_dashboard_cache: dict[int, tuple[float, dict[str, Any]]] = {}


def get_portfolio_dashboard_data(portfolio_id: int) -> dict[str, Any]:
    now = monotonic()
    cached_entry = _dashboard_cache.get(portfolio_id)

    if cached_entry is not None:
        cached_at, cached_data = cached_entry

        if now - cached_at < DASHBOARD_CACHE_TTL_SECONDS:
            logger.info(
                "Dashboard cache hit for portfolio_id=%s age_seconds=%.3f",
                portfolio_id,
                now - cached_at,
            )
            return deepcopy(cached_data)

    build_started_at = monotonic()
    dashboard_data = _build_portfolio_dashboard_data(portfolio_id)
    build_duration = monotonic() - build_started_at
    cached_at = monotonic()
    _dashboard_cache[portfolio_id] = (cached_at, dashboard_data)
    logger.info(
        "Dashboard cache miss for portfolio_id=%s build_duration_seconds=%.3f",
        portfolio_id,
        build_duration,
    )
    return deepcopy(dashboard_data)


def invalidate_portfolio_dashboard_cache(portfolio_id: int) -> None:
    _dashboard_cache.pop(portfolio_id, None)


def invalidate_all_dashboard_cache() -> None:
    _dashboard_cache.clear()


def clear_dashboard_cache() -> None:
    _dashboard_cache.clear()


def _build_portfolio_dashboard_data(portfolio_id: int) -> dict[str, Any]:
    risk = _timed_dashboard_step(
        portfolio_id,
        "risk",
        calculate_portfolio_risk,
    )
    returns = _timed_dashboard_step(
        portfolio_id,
        "returns",
        calculate_portfolio_returns,
    )
    holdings = _timed_dashboard_step(
        portfolio_id,
        "holdings",
        calculate_portfolio_holdings,
    )
    sector_exposure = _timed_dashboard_step(
        portfolio_id,
        "sector_exposure",
        calculate_sector_exposure,
    )
    risk_contribution = _timed_dashboard_step(
        portfolio_id,
        "risk_contribution",
        calculate_risk_contribution,
    )

    return {
        "risk": risk,
        "returns": returns,
        "holdings": holdings,
        "sector_exposure": sector_exposure,
        "risk_contribution": risk_contribution,
    }


def _timed_dashboard_step(portfolio_id: int, name: str, func):
    started_at = monotonic()
    result = func(portfolio_id)
    logger.info(
        "Dashboard step completed portfolio_id=%s step=%s duration_seconds=%.3f",
        portfolio_id,
        name,
        monotonic() - started_at,
    )
    return result
