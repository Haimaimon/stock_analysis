from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple, Set
import pandas as pd
import pytz

from ...domain.entities import Signal
from ...domain.ports import MarketDataFeed, AlertSink
from ..strategies.base_strategy import BaseStrategy
from .trading import TradeExecutor, RiskManager, TradeConfig
import logging, numpy as np, pandas as pd, pytz
log = logging.getLogger(__name__)

US_EASTERN = pytz.timezone("US/Eastern")
def _as_float(x):
    if isinstance(x, pd.Series):
        x = x.iloc[-1] if len(x) else np.nan
    if hasattr(x, "item"):
        try:
            x = x.item()
        except Exception:
            pass
    try:
        return float(x)
    except Exception:
        return float("nan")
@dataclass
class EngineConfig:
    tickers: List[str]
    price_range: Optional[Tuple[float, float]] = None # e.g., (8.0, 14.0)
    days_history_5m: int = 10
    poll_interval_sec: int = 30
    stop_after_minutes: int = 25

    # חדש – Risk/Trade
    position_size: int = 100
    tp_pct: float = 0.02
    sl_pct: float = 0.01

@dataclass
class LiveEngine:
    feed: MarketDataFeed
    sink: AlertSink
    strategy: BaseStrategy
    cfg: EngineConfig
    _signaled: Set[str] = field(default_factory=set)

    def __init__(self, feed, sink, strategy, cfg: EngineConfig):
        self.feed = feed
        self.sink = sink
        self.strategy = strategy
        self.cfg = cfg
        self._signaled: set[str] = set()

        self.trade_cfg = TradeConfig(
            position_size=cfg.position_size,
            tp_pct=cfg.tp_pct,
            sl_pct=cfg.sl_pct,
            check_interval_sec=15,
        )
        self.executor = TradeExecutor(sink=self.sink)
        self.risk = RiskManager(feed=self.feed, sink=self.sink, executor=self.executor, cfg=self.trade_cfg)

    async def _filter_by_price(self, tickers: List[str]) -> List[str]:
        log.info("💡 price filter | range=%s | candidates=%d", self.cfg.price_range, len(tickers))
        if not self.cfg.price_range:
            return tickers
        lo, hi = self.cfg.price_range
        res: List[str] = []
        for t in tickers:
            df = await self.feed.get_5m_history(t, days=2)
            if df.empty:
             continue
            val = df["Close"].iloc[-1]
            last_close = val.item() if hasattr(val, "item") else float(val)
            if lo <= last_close <= hi:
                res.append(t)
        return res


    def _market_open_reached(self) -> bool:
        now_et = datetime.now(US_EASTERN).time()
        return now_et >= time(9, 30)


    async def run(self) -> None:
        # המתנה לפתיחת שוק אם הופעל לפני 09:30 ET
        log.info("🚀 LiveEngine starting")
        while not self._market_open_reached():
            await asyncio.sleep(5)

        # הפעלת Risk Manager ברקע
        asyncio.create_task(self.risk.start())

        watchlist = await self._filter_by_price(self.cfg.tickers)
        start_ts = datetime.now(US_EASTERN)
        log.info("🔭 scanning watchlist | size=%d", len(watchlist))


        while (datetime.now(US_EASTERN) - start_ts) < timedelta(minutes=self.cfg.stop_after_minutes):
            tasks = [self._scan_one(t) for t in watchlist]
            await asyncio.gather(*tasks)
            await asyncio.sleep(self.cfg.poll_interval_sec)

    
    async def _scan_one(self, ticker: str) -> None:
        if ticker in self._signaled:
            return

        df5 = await self.feed.get_5m_history(ticker, days=self.cfg.days_history_5m)
        if df5.empty:
            log.debug("[%s] empty df", ticker); return

        should, reason = self.strategy.evaluate_opening_bar(df5)
        log.info("[%s] strategy result | should=%s | %s", ticker, should, reason)

        if not should:
            return

        # --- חילוץ נר פתיחה של היום + לוגים ברורים ---
        today_date = pd.Timestamp.now(tz=US_EASTERN).date()
        idx_dates = df5.index.tz_convert(US_EASTERN).date
        today_df = df5[idx_dates == today_date]

        if today_df.empty:
            log.warning("[%s] today_df empty at signal time", ticker)
            return

        open_bar = today_df.iloc[0]  # נר 09:35-09:40 בד"כ
        ob_open  = _as_float(open_bar["Open"])
        ob_high  = _as_float(open_bar["High"])
        ob_low   = _as_float(open_bar["Low"])
        ob_close = _as_float(open_bar["Close"])

        log.info("[%s] opening bar | O=%.4f H=%.4f L=%.4f C=%.4f | ts=%s",
                 ticker, ob_open, ob_high, ob_low, ob_close, str(today_df.index[0]))

        entry_price = ob_close  # או ob_high אם כך הכלל
        if np.isnan(entry_price):
            log.warning("[%s] entry nan, fallback to last close", ticker)
            last = df5["Close"].iloc[-1]
            entry_price = _as_float(last)

        log.info("[%s] 📈 opening position | entry=%.4f", ticker, entry_price)
        await self.executor.open_long(ticker, entry_price, self.trade_cfg)
        self._signaled.add(ticker)
