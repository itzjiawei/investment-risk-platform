from fastapi import APIRouter

from app.database.repository import (
    load_assets,
    load_holdings,
    load_portfolios,
    load_prices,
)


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
