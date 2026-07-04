import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

np.random.seed(42)

assets = pd.DataFrame([
    [1, "AAPL", "Apple", "Technology", "US", "AAPL"],
    [2, "MSFT", "Microsoft", "Technology", "US", "MSFT"],
    [3, "NVDA", "NVIDIA", "Semiconductors", "US", "NVDA"],
    [4, "TSMC", "TSMC", "Semiconductors", "Taiwan", "2330.TW"],
    [5, "DBS", "DBS Bank", "Financials", "Singapore", "D05.SI"],
    [6, "TENCENT", "Tencent", "Technology", "China", "0700.HK"],
    [7, "SPY", "S&P 500 ETF", "ETF", "US", "SPY"],
    [8, "GLD", "Gold ETF", "Commodities", "US", "GLD"],
], columns=[
    "asset_id",
    "ticker",
    "name",
    "sector",
    "country",
    "yfinance_ticker",
])

portfolios = pd.DataFrame([
    [1, "Global Growth Portfolio"],
    [2, "Asia Balanced Portfolio"],
], columns=["portfolio_id", "portfolio_name"])

holdings = pd.DataFrame([
    [1, 1, 100],
    [1, 2, 80],
    [1, 3, 60],
    [1, 7, 150],
    [1, 8, 90],

    [2, 4, 120],
    [2, 5, 500],
    [2, 6, 200],
    [2, 7, 100],
    [2, 8, 120],
], columns=["portfolio_id", "asset_id", "quantity"])

start_prices = {
    1: 180,
    2: 360,
    3: 850,
    4: 130,
    5: 35,
    6: 300,
    7: 500,
    8: 190,
}

dates = pd.date_range(start="2023-01-01", end="2025-12-31", freq="B")

price_rows = []

for asset_id, start_price in start_prices.items():
    price = start_price

    for date in dates:
        daily_return = np.random.normal(loc=0.0004, scale=0.018)
        price = price * (1 + daily_return)
        price = max(price, 1)

        price_rows.append([
            asset_id,
            date.strftime("%Y-%m-%d"),
            round(price, 2)
        ])

prices = pd.DataFrame(price_rows, columns=["asset_id", "date", "close_price"])

assets.to_csv(DATA_DIR / "assets.csv", index=False)
portfolios.to_csv(DATA_DIR / "portfolios.csv", index=False)
holdings.to_csv(DATA_DIR / "holdings.csv", index=False)
prices.to_csv(DATA_DIR / "prices.csv", index=False)

print("Demo data generated successfully!")
print(f"Assets: {len(assets)}")
print(f"Portfolios: {len(portfolios)}")
print(f"Holdings: {len(holdings)}")
print(f"Price rows: {len(prices)}")
