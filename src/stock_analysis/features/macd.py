# src/stock_analysis/features/macd.py
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass
class MACD:
    span_fast: int = 12
    span_slow: int = 26
    out_col: str = "MACD"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        ema_fast = df["Close"].ewm(span=self.span_fast).mean()
        ema_slow = df["Close"].ewm(span=self.span_slow).mean()
        out = df.copy()
        out[self.out_col] = ema_fast - ema_slow
        return out

def compute_macd_last(close: pd.Series, span_fast: int = 12, span_slow: int = 26) -> float:
    ema_fast = close.ewm(span=span_fast).mean()
    ema_slow = close.ewm(span=span_slow).mean()
    return float((ema_fast - ema_slow).iloc[-1])
