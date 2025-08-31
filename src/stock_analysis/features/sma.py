# src/stock_analysis/features/sma.py
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass
class SMA:
    window: int
    out_col: str | None = None

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        col = self.out_col or f"SMA_{self.window}"
        out[col] = out["Close"].rolling(self.window).mean()
        return out
