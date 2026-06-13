import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
np.random.seed(42)

num_assets = 1000
num_days = 1000

dates = pd.date_range(start="2020-01-01", periods=num_days, freq="B")

assets = pd.DataFrame({
    "asset_id": range(1, num_assets + 1),
    "ticker": [f"AST{i}" for i in range(1, num_assets + 1)],
    "name": [f"Asset {i}" for i in range(1, num_assets + 1)],
    "sector": np.random.choice(
        ["Technology", "Financials", "Healthcare", "ETF", "Commodities"],
        size=num_assets
    ),
    "country": np.random.choice(
        ["US", "Singapore", "China", "Japan", "UK"],
        size=num_assets
    ),
})

holdings = pd.DataFrame({
    "portfolio_id": [99] * 300,
    "asset_id": np.random.choice(range(1, num_assets + 1), size=300, replace=False),
    "quantity": np.random.randint(10, 1000, size=300),
})

price_rows = []

for asset_id in range(1, num_assets + 1):
    price = np.random.uniform(20, 500)

    for date in dates:
        daily_return = np.random.normal(0.0003, 0.02)
        price = max(price * (1 + daily_return), 1)

        price_rows.append([
            asset_id,
            date.strftime("%Y-%m-%d"),
            round(price, 2)
        ])

prices = pd.DataFrame(price_rows, columns=["asset_id", "date", "close_price"])

assets.to_csv(DATA_DIR / "large_assets.csv", index=False)
holdings.to_csv(DATA_DIR / "large_holdings.csv", index=False)
prices.to_csv(DATA_DIR / "large_prices.csv", index=False)

print("Large data generated")
print(f"Assets: {len(assets)}")
print(f"Holdings: {len(holdings)}")
print(f"Prices: {len(prices)}")