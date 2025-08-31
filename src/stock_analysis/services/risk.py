from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass
class TradePlan:
    symbol: str
    entry: float
    stop: float
    target: float
    risk_per_share: float
    rr: float  # Reward/Risk
    position_size_usd: float
    shares: int
    reason: str = ""

def build_trade_plan(
    symbol: str,
    entry: float,
    atr: float | None,
    atr_mult_stop: float = 1.2,
    rr_ratio: float = 2.0,
    risk_budget_usd: float = 100.0,
    min_atr_abs: float = 0.05,            # NEW: מינימום מרחק סטופ בדולרים
    max_shares_per_trade: int = 1000,     # NEW: תקרת כמות מניות לעסקה
) -> TradePlan | None:
    if entry is None or atr is None or atr <= 0:
        return None

    # סטופ – לוקחים את המקסימום בין ATR*mult לבין מינימום אבסולוטי
    stop_dist = max(atr_mult_stop * float(atr), float(min_atr_abs))
    stop = entry - stop_dist
    risk_per_share = max(0.01, entry - stop)  # רשת ביטחון
    target = entry + rr_ratio * risk_per_share

    shares = int(risk_budget_usd // risk_per_share) if risk_per_share > 0 else 0
    shares = min(max_shares_per_trade, shares)

    return TradePlan(
        symbol=symbol,
        entry=entry,
        stop=stop,
        target=target,
        risk_per_share=risk_per_share,
        rr=rr_ratio,
        position_size_usd=shares * entry,
        shares=shares,
        reason="" if shares > 0 else "risk too small",
    )
