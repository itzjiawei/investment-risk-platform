from pathlib import Path
import pandas as pd

from app.database import engine

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

tables = {
    "assets": DATA_DIR / "assets.csv",
    "portfolios": DATA_DIR / "portfolios.csv",
    "holdings": DATA_DIR / "holdings.csv",
    "prices": DATA_DIR / "prices.csv",
}

for table_name, file_path in tables.items():
    df = pd.read_csv(file_path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"Loaded {table_name}: {len(df)} rows")

print("Database seeded successfully")