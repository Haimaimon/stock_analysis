from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import pandas as pd
import pytz

from ...domain.trading import Position, Side, PositionStatus
from ...domain.entities import Signal
from ...domain.ports import MarketDataFeed, AlertSink
from ...infrastructure.sinks.streamlit_state import save_positions

US_EASTERN = pytz.timezone("US/Eastern")

@dataclass
class TradeConfig:
    position_size: int = 100         # כמות מניה לפתיחה
    tp_pct: float = 0.02             # 2% רווח
    sl_pct: float = 0.01             # 1% הפסד
    check_interval_sec: int = 15     # כל כמה זמן לבדוק TP/SL

@dataclass
class TradeExecutor:
    sink: AlertSink
    positions: Dict[str, Position] = field(default_factory=dict)  # לפי ticker אחד פתוח

    async def open_long(self, ticker: str, price: float, cfg: TradeConfig) -> Position:
        if ticker in self.positions and self.positions[ticker].status == PositionStatus.OPEN:
            return self.positions[ticker]  # כבר פתוח

        tp = price * (1.0 + cfg.tp_pct)
        sl = price * (1.0 - cfg.sl_pct)
        pos = Position(
            ticker=ticker,
            side=Side.LONG,
            qty=cfg.position_size,
            entry_price=price,
            tp_price=tp,
            sl_price=sl,
            opened_at=datetime.now(US_EASTERN),
        )
        self.positions[ticker] = pos
        await self.sink.emit(Signal(
            ticker=ticker,
            ts=datetime.now(US_EASTERN),
            reason=f"OPEN LONG qty={pos.qty} @ {price:.2f} | TP={tp:.2f}, SL={sl:.2f}"
        ))
        save_positions(self.positions)
        return pos

    async def close(self, ticker: str, price: float, reason: str) -> Optional[Position]:
        pos = self.positions.get(ticker)
        if not pos or pos.status == PositionStatus.CLOSED:
            return None
        pos.status = PositionStatus.CLOSED
        pos.exit_price = price
        pos.closed_at = datetime.now(US_EASTERN)
        await self.sink.emit(Signal(
            ticker=ticker,
            ts=datetime.now(US_EASTERN),
            reason=f"CLOSE @ {price:.2f} | PnL={pos.pnl_abs:.2f} USD ({pos.pnl_pct:.2f}%) | {reason}"
        ))
        save_positions(self.positions)
        return pos

@dataclass
class RiskManager:
    feed: MarketDataFeed
    sink: AlertSink
    executor: TradeExecutor
    cfg: TradeConfig

    async def start(self):
        # לולאה מתמשכת: בודק TP/SL לכל פוזיציה פתוחה
        while True:
            await self._scan_all()
            await asyncio.sleep(self.cfg.check_interval_sec)

    async def _scan_all(self):
        open_tickers = [t for t, p in self.executor.positions.items() if p.status == PositionStatus.OPEN]
        if not open_tickers:
            return
        tasks = [self._scan_one(t) for t in open_tickers]
        await asyncio.gather(*tasks)

    async def _scan_one(self, ticker: str):
        pos = self.executor.positions.get(ticker)
        if not pos or pos.status != PositionStatus.OPEN:
            return
        # מחיר עדכני: לוקח את Close האחרון מהיסטוריית 5m
        df = await self.feed.get_5m_history(ticker, days=1)
        if df.empty:
            return
        last = df.iloc[-1]["Close"]
        price = float(last.item() if hasattr(last, "item") else last)

        if price >= pos.tp_price:
            await self.executor.close(ticker, price, reason="Hit TP")
        elif price <= pos.sl_price:
            await self.executor.close(ticker, price, reason="Hit SL")
