from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class AppConfig:
    tickers: List[str]
    price_range: Optional[Tuple[float, float]] = (8.0, 14.0)
    days_history_5m: int = 10
    poll_interval_sec: int = 30
    stop_after_minutes: int = 25
    position_size: int = 100
    tp_pct: float = 0.02
    sl_pct: float = 0.01