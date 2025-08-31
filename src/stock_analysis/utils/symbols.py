# src/stock_analysis/utils/symbols.py
from __future__ import annotations
import os, pandas as pd
from stock_analysis.infrastructure.data.sp500 import refresh_sp500_prices
from stock_analysis.infrastructure.data.nasdaq import refresh_nasdaq_prices

def fetch_symbols_with_price_range(min_price: float, max_price: float, csv_path: str = "sp500_prices.csv"):
    if not os.path.exists(csv_path):
        if "nasdaq" in csv_path.lower():
            refresh_nasdaq_prices(csv_path)
        else:
            refresh_sp500_prices(csv_path)
    df = pd.read_csv(csv_path)
    return df[(df["Price"] >= min_price) & (df["Price"] <= max_price)]["Symbol"].tolist()

def load_sp500_symbols(path: str = "sp500_prices.csv"):
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df["Symbol"].tolist()
    return []

def load_nasdaq_symbols(path: str = "nasdaq_all.csv"):
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df["Symbol"].tolist()
    return []
