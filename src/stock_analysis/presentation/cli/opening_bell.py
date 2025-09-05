# opening_bell_entry.py (או עדכן את הקיים שלך)
from __future__ import annotations
import os, asyncio, logging, logging.config
from pathlib import Path
import pandas as pd

from .. import __package__ as _pkg
from ...application.config import AppConfig
from ...application.services.live_engine import LiveEngine, EngineConfig
from ...application.strategies.opening_bell_strategy import OpeningBellStrategy
from ...infrastructure.feeds.yfinance_feed import YFinanceFeed
from ...infrastructure.sinks.console_sink import ConsoleSink
from ...infrastructure.sinks.streamlit_sink import StreamlitSink
from ...infrastructure.sinks.multi_sink import MultiSink
# ייבוא טלגרם ייעשה עצל בתוך הקוד (לא חובה), כדי לא להפיל אם חסר:
def _maybe_telegram_sink():
    try:
        from ...infrastructure.sinks.telegram_sink import TelegramSink
        token = os.getenv("TELEGRAM_BOT_TOKEN", "8266591169:AAEbZZ1UO4-AOoK7rI4ci9Vv8sTtK7GuOZc")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "8075458483")
        if token and chat_id:
            return TelegramSink(token=token, chat_id=chat_id)
    except Exception:
        pass
    return None

from ...infrastructure.data.universes import load_watchlist, load_nasdaq_symbols

LOG_CFG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"std": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"}},
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
    "loggers": {
        "stock_analysis.infrastructure.feeds.yfinance_feed": {"level": "INFO"},
        "stock_analysis.application.services.live_engine": {"level": "DEBUG"},
        "stock_analysis.application.strategies.opening_bell_strategy": {"level": "DEBUG"},
        "stock_analysis.application.services.trading": {"level": "INFO"},
    },
}
logging.config.dictConfig(LOG_CFG)

def _load_universe() -> list[str]:
    universe = os.getenv("UNIVERSE", "WATCHLIST").strip().upper()  # WATCHLIST | NASDAQ
    max_n = int(os.getenv("MAX_TICKERS", "1200"))  # אל תרוץ ישר על 6200 בחינם
    if universe == "NASDAQ":
        syms = load_nasdaq_symbols(max_n=max_n)
        if not syms:
            logging.warning("NASDAQ list empty; falling back to watchlist.csv")
            syms = load_watchlist()
    else:
        syms = load_watchlist()
    if not syms:
        # fallback קשיח
        syms = ["AAPL","MSFT","NVDA","PLTR","SOFI","F","CSX","FAST","FOX","NI"]
    return syms

async def main() -> None:
    # === פרמטרים שניתן לשנות ב-ENV בלי לגעת בקוד ===
    PRICE_MIN = float(os.getenv("PRICE_MIN", "2.0"))
    PRICE_MAX = float(os.getenv("PRICE_MAX", "250.0"))
    DAYS_5M   = int(os.getenv("DAYS_5M", "10"))
    POLL_SEC  = int(os.getenv("POLL_SEC", "30"))
    STOP_MIN  = int(os.getenv("STOP_MIN", "60"))  # העליתי ל-60 כדי לא לפספס פתיחה
    POS_SIZE  = int(os.getenv("POS_SIZE", "100"))
    TP_PCT    = float(os.getenv("TP_PCT", "0.02"))
    SL_PCT    = float(os.getenv("SL_PCT", "0.01"))

    tickers = _load_universe()

    sinks = [ConsoleSink(), StreamlitSink()]
    tg = _maybe_telegram_sink()
    if tg: sinks.append(tg)
    sink = MultiSink(sinks)

    engine = LiveEngine(
        feed=YFinanceFeed(),  # עם RateLimiter בפנים
        sink=sink,
        strategy=OpeningBellStrategy(),
        cfg=EngineConfig(
            tickers=tickers,
            price_range=(PRICE_MIN, PRICE_MAX),
            days_history_5m=DAYS_5M,
            poll_interval_sec=POLL_SEC,
            stop_after_minutes=STOP_MIN,
            position_size=POS_SIZE,
            tp_pct=TP_PCT,
            sl_pct=SL_PCT,
        ),
    )

    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())
