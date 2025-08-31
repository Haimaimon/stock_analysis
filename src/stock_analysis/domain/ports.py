from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import pandas as pd


class MarketDataFeed(ABC):
    @abstractmethod
    async def get_5m_history(self, ticker: str, days: int = 10) -> pd.DataFrame:
        """Return 5m OHLCV DataFrame tz-aware (US/Eastern) for recent days (incl. today)."""
        raise NotImplementedError


class AlertSink(ABC):
    @abstractmethod
    async def emit(self, signal: "Signal") -> None:
        raise NotImplementedError