from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class StrategySignal:
    symbol: str
    strategy: str
    open_time: str
    open_price: float | None
    prev_close: float | None
    gap_pct: float | None
    rvol: float | None
    vwap_ok: bool | None
    sma20: float | None
    sma200: float | None
    reason: str | None
    decision: str  # "BUY"/"HOLD"


@dataclass(frozen=True)
class Signal:
    ticker: str
    ts: datetime
    reason: str


# שמור על הדומיין נקי מתלויות חיצוניות (ללא pandas וכו').
# נרות/ברֵים מיוצגים בשכבות העליונות (Application/Infrastructure) לפי הצורך.