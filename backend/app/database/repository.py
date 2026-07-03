import pandas as pd
from sqlalchemy import text

from app.database.config import engine


def load_assets():
    query = text("SELECT * FROM assets")
    return pd.read_sql(query, engine)


def load_portfolios():
    query = text("SELECT * FROM portfolios")
    return pd.read_sql(query, engine)


def load_holdings():
    query = text("SELECT * FROM holdings")
    return pd.read_sql(query, engine)


def load_prices():
    query = text("SELECT * FROM prices")
    return pd.read_sql(query, engine)
