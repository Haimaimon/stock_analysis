# src/stock_analysis/infrastructure/business/holders_yf.py
from __future__ import annotations
from typing import List
import yfinance as yf
from stock_analysis.domain.interfaces import HoldersProvider

class YFinanceHoldersProvider(HoldersProvider):
    def top_institutional_holders(self, symbol: str, top_n: int = 5) -> List[str]:
        try:
            t = yf.Ticker(symbol)
            holders = t.institutional_holders
            if holders is not None and "Holder" in holders.columns:
                return list(holders["Holder"].head(top_n))
        except Exception:
            pass
        return ["N/A"]
