from __future__ import annotations
import asyncio
from .. import __package__ as _pkg
from ...application.config import AppConfig
from ...application.services.live_engine import LiveEngine, EngineConfig
from ...application.strategies.opening_bell_strategy import OpeningBellStrategy
from ...infrastructure.feeds.yfinance_feed import YFinanceFeed
from ...infrastructure.sinks.console_sink import ConsoleSink
# מאוחר יותר ניתן להחליף ConsoleSink ל-TelegramSink בקלות
from ...infrastructure.sinks.telegram_sink import TelegramSink
from ...infrastructure.sinks.streamlit_sink import StreamlitSink
from ...infrastructure.sinks.multi_sink import MultiSink
import logging, logging.config
import pandas as pd

from pathlib import Path

LOG_CFG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "std": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "std", "level": "INFO"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "std",
            "level": "DEBUG",
            "filename": "opening_bell.log",
            "maxBytes": 3_000_000,
            "backupCount": 3,
            "encoding": "utf-8",
        },
    },
    "root": {"level": "INFO", "handlers": ["console", "file"]},
    # אפשר לכוון רמות לפי מודולים:
    "loggers": {
        "stock_analysis.infrastructure.feeds.yfinance_feed": {"level": "INFO"},
        "stock_analysis.application.services.live_engine": {"level": "DEBUG"},   # יותר פירוט
        "stock_analysis.application.strategies.opening_bell_strategy": {"level": "DEBUG"},
        "stock_analysis.application.services.trading": {"level": "INFO"},
    },
}
logging.config.dictConfig(LOG_CFG)

WATCHLIST_FILE = Path("data/watchlist.csv")

if WATCHLIST_FILE.exists():
    DEFAULT_TICKERS = pd.read_csv(WATCHLIST_FILE)["Symbol"].tolist()
else:
    DEFAULT_TICKERS = ["AAPL","MSFT","NVDA","PLTR","SOFI","F","CSX","FAST","FOX","NI"]

async def main() -> None:
    cfg = AppConfig(
    tickers=DEFAULT_TICKERS,
    price_range=(2.0, 250.0),
    days_history_5m=10,
    poll_interval_sec=30,
    stop_after_minutes=25,
    position_size=100,
    tp_pct=0.02,
    sl_pct=0.01,
    )
    
    sink = MultiSink([
        ConsoleSink(),
        StreamlitSink(),
        TelegramSink(token="8266591169:AAEbZZ1UO4-AOoK7rI4ci9Vv8sTtK7GuOZc", chat_id="8075458483")    
    ])

    engine = LiveEngine(
        feed=YFinanceFeed(),
        sink = sink,
        strategy=OpeningBellStrategy(),
        cfg=EngineConfig(
        tickers=cfg.tickers,
        price_range=cfg.price_range,
        days_history_5m=cfg.days_history_5m,
        poll_interval_sec=cfg.poll_interval_sec,
        stop_after_minutes=cfg.stop_after_minutes,
        position_size=cfg.position_size,
        tp_pct=cfg.tp_pct,
        sl_pct=cfg.sl_pct,
        ),
    ) 


    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())