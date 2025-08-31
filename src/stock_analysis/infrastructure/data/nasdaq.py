# src/stock_analysis/infrastructure/data/nasdaq.py
from __future__ import annotations
import pandas as pd, os

def refresh_nasdaq_prices(nasdaq_csv_path: str = "nasdaq_all.csv", original_nasdaq_file: str = "nasdaq_all.csv"):
    if os.path.exists(original_nasdaq_file):
        df = pd.read_csv(original_nasdaq_file)
        df = df[["Symbol", "Price"]]
        df.to_csv(nasdaq_csv_path, index=False)
