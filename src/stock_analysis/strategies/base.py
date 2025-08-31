from __future__ import annotations
from typing import Protocol
import pandas as pd
from stock_analysis.domain.interfaces import DataProvider

class Strategy(Protocol):
    """ממשק אסטרטגיה אינטראדיי: מפיקה DataFrame של נרות + עמודות חישוב/סיגנל."""
    def run(
        self,
        symbol: str,
        data_provider: DataProvider,
        period: str = "5d",
        interval: str = "5m",
    ) -> pd.DataFrame: ...
