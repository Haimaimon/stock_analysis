from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class Side(str, Enum):
    LONG = "LONG"

class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

@dataclass
class Position:
    ticker: str
    side: Side
    qty: int
    entry_price: float
    tp_price: float
    sl_price: float
    opened_at: datetime
    status: PositionStatus = PositionStatus.OPEN
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None

    @property
    def pnl_abs(self) -> Optional[float]:
        if self.exit_price is None:
            return None
        sign = 1 if self.side == Side.LONG else -1
        return (self.exit_price - self.entry_price) * self.qty * sign

    @property
    def pnl_pct(self) -> Optional[float]:
        if self.exit_price is None:
            return None
        sign = 1 if self.side == Side.LONG else -1
        return sign * (self.exit_price / self.entry_price - 1.0) * 100.0
