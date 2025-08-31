# src/stock_analysis/infrastructure/data_providers/yfinance_provider.py
from __future__ import annotations
import pandas as pd
import yfinance as yf
from typing import Mapping, Any

class YFinanceProvider:
    def info(self, symbol: str) -> Mapping[str, Any]:
        t = yf.Ticker(symbol)
        return t.info or {}

    def history(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        t = yf.Ticker(symbol)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        return df

    def last_price(self, symbol: str) -> float | None:
        t = yf.Ticker(symbol)
        info = t.info or {}
        return info.get("currentPrice")
