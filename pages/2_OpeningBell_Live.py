# pages/2_OpeningBell_Live.py
import streamlit as st
import asyncio
import logging, logging.config
from pathlib import Path
import pandas as pd

# ===== Imports מהחבילה שלך (אבסולוטי) =====
from stock_analysis.application.config import AppConfig
from stock_analysis.application.services.live_engine import LiveEngine, EngineConfig
from stock_analysis.application.strategies.opening_bell_strategy import OpeningBellStrategy
from stock_analysis.infrastructure.feeds.yfinance_feed import YFinanceFeed
from stock_analysis.infrastructure.sinks.console_sink import ConsoleSink
from stock_analysis.infrastructure.sinks.telegram_sink import TelegramSink
from stock_analysis.infrastructure.sinks.streamlit_sink import StreamlitSink
from stock_analysis.infrastructure.sinks.multi_sink import MultiSink

# ===== לוגים (קובץ יישמר באחסון ארעי של Streamlit Cloud) =====
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

def _load_default_tickers() -> list[str]:
    p = Path("data/watchlist.csv")
    if p.exists():
        try:
            return (
                pd.read_csv(p)["Symbol"]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
                .tolist()
            )
        except Exception:
            pass
    return ["AAPL","MSFT","NVDA","PLTR","SOFI","F","CSX","FAST","FOX","NI"]

def _build_sink(use_console: bool, use_streamlit: bool, use_telegram: bool):
    sinks = []
    if use_console:
        sinks.append(ConsoleSink())
    if use_streamlit:
        sinks.append(StreamlitSink())  # משתמש ברכיבי Streamlit להצגה
    if use_telegram:
        token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            sinks.append(TelegramSink(token=token, chat_id=str(chat_id)))
        else:
            st.warning("בחרת Telegram אבל TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID לא הוגדרו ב-Secrets.")
    if not sinks:
        sinks.append(ConsoleSink())
    return MultiSink(sinks) if len(sinks) > 1 else sinks[0]

def run_engine(
    tickers: list[str],
    price_range: tuple[float, float],
    days_history_5m: int,
    poll_interval_sec: int,
    stop_after_minutes: int,
    position_size: int,
    tp_pct: float,
    sl_pct: float,
    use_console: bool,
    use_streamlit: bool,
    use_telegram: bool,
):
    # AppConfig לא חובה פה, אם אתה משתמש בו מאוחר יותר אתה יכול לשלב
    sink = _build_sink(use_console, use_streamlit, use_telegram)
    engine = LiveEngine(
        feed=YFinanceFeed(),
        sink=sink,
        strategy=OpeningBellStrategy(),
        cfg=EngineConfig(
            tickers=tickers,
            price_range=price_range,
            days_history_5m=days_history_5m,
            poll_interval_sec=poll_interval_sec,
            stop_after_minutes=stop_after_minutes,
            position_size=position_size,
            tp_pct=tp_pct,
            sl_pct=sl_pct,
        ),
    )
    # ריצה סינכרונית (תיחסם עד סיום/עצירה). בסביבת Streamlit זה תקין
    return asyncio.run(engine.run())

def main():
    st.set_page_config(page_title="🔔 Opening Bell – Live", layout="wide")
    st.title("🔔 Opening Bell – Live Engine")

    defaults = _load_default_tickers()
    st.caption(f"ברירת מחדל: {len(defaults)} טיקרים (ניתן לשנות)")

    # ===== UI =====
    selected = st.multiselect("בחר טיקרים", options=sorted(defaults), default=defaults[:10])
    extra = st.text_input("טיקרים נוספים (מופרדים בפסיק):", "")
    if extra.strip():
        selected += [t.strip().upper() for t in extra.split(",") if t.strip()]

    c1, c2, c3 = st.columns(3)
    with c1:
        price_min, price_max = st.slider("טווח מחיר", 1.0, 500.0, (2.0, 250.0))
        days_5m = st.number_input("היסטוריית 5m (ימים)", 1, 30, 10, step=1)
    with c2:
        poll = st.number_input("מרווח בדיקה (שנ׳)", 10, 300, 30, step=5)
        stop_after = st.number_input("עצור אחרי (דקות)", 5, 180, 25, step=5)
    with c3:
        pos_size = st.number_input("גודל פוזיציה", 1, 10_000, 100, step=10)
        tp = st.number_input("TP %", 0.1, 10.0, 2.0, step=0.1) / 100.0
        sl = st.number_input("SL %", 0.1, 10.0, 1.0, step=0.1) / 100.0

    st.markdown("**ערוצי פלט:**")
    s1, s2, s3 = st.columns(3)
    with s1:
        use_console = st.checkbox("Console", True)
    with s2:
        use_stream = st.checkbox("Streamlit", True)
    with s3:
        use_tg = st.checkbox("Telegram", False)

    run = st.button("▶️ הפעל Live Engine", use_container_width=True)
    if run:
        if not selected:
            st.error("בחר לפחות טיקר אחד.")
            st.stop()
        with st.spinner("מריץ את המנוע... (יעצור אוטומטית בהתאם להגדרות)"):
            try:
                run_engine(
                    tickers=selected,
                    price_range=(price_min, price_max),
                    days_history_5m=int(days_5m),
                    poll_interval_sec=int(poll),
                    stop_after_minutes=int(stop_after),
                    position_size=int(pos_size),
                    tp_pct=float(tp),
                    sl_pct=float(sl),
                    use_console=use_console,
                    use_streamlit=use_stream,
                    use_telegram=use_tg,
                )
                st.success("המנוע הסתיים.")
            except Exception as e:
                st.exception(e)

if __name__ == "__main__":
    main()
