# src/stock_analysis/features/rsi.py
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass
class RSI:
    period: int = 14
    out_col: str = "RSI"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        s = df["Close"]
        delta = s.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        out = df.copy()
        out[self.out_col] = rsi
        return out

def compute_rsi_last(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])
