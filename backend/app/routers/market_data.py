from fastapi import APIRouter

from app.database.repository import (
    load_assets,
    load_holdings,
    load_portfolios,
    load_prices,
)
from app.services.market_data_service import (
    get_market_data_status,
    refresh_market_data,
)
from app.services.dashboard_cache_service import invalidate_all_dashboard_cache


router = APIRouter(prefix="/api")


@router.get("/assets")
def get_assets():
    assets = load_assets()
    return assets.to_dict(orient="records")


@router.get("/portfolios")
def get_portfolios():
    portfolios = load_portfolios()
    return portfolios.to_dict(orient="records")


@router.get("/holdings")
def get_holdings():
    holdings = load_holdings()
    return holdings.to_dict(orient="records")


@router.get("/prices")
def get_prices(limit: int = 20):
    prices = load_prices()
    return prices.head(limit).to_dict(orient="records")


@router.post("/market-data/refresh")
def refresh_market_prices():
    result = refresh_market_data()
    invalidate_all_dashboard_cache()
    return result


@router.get("/market-data/status")
def get_market_prices_status():
    return get_market_data_status()
