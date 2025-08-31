import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
# --- ensure package import works when running via `streamlit run` ---
import sys, os
PROJECT_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if PROJECT_SRC not in sys.path:
    sys.path.insert(0, PROJECT_SRC)
# -------------------------------------------------------------------

from stock_analysis.presentation.streamlit.partials.countdown import render_open_countdown

DATA_DIR = Path("data")
SIGNALS_FILE = DATA_DIR / "signals.jsonl"

st.set_page_config(page_title="Opening Bell Live", layout="wide")
st.title("🔔 Opening Bell Live – Signals & Positions")
render_open_countdown()
st.divider()

# רענון אוטומטי כל 5 שניות
st.caption("Auto-refresh every 5s")
# רענון אוטומטי כל 5 שניות (אם הפונקציה קיימת בגרסה שלך)
try:
    st.autorefresh(interval=5000, key="main_autorefresh")
except Exception:
    pass  # בגרסאות ישנות יותר פשוט נתבסס על רענון ידני או על ה-countdown שמרענן בעצמו


st.write("")

# טוען אותות
signals = []
if SIGNALS_FILE.exists():
    with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                signals.append(json.loads(line))
            except:
                pass

col1, col2 = st.columns([2,1], gap="large")

with col1:
    st.subheader("Live Signals")
    if signals:
        df = pd.DataFrame(signals)
        # עיצוב זמן קריא
        df["ts"] = pd.to_datetime(df["ts"])
        df = df.sort_values("ts", ascending=False).reset_index(drop=True)
        st.dataframe(df, use_container_width=True, height=380)
    else:
        st.info("No signals yet. Waiting for market open or strategy trigger...")

with col2:
    st.subheader("Positions (paper)")
    # קורא מצב פוזיציות מה-TradeExecutor דרך קובץ JSON שמעדכן ה-Engine
    POS_FILE = DATA_DIR / "positions.json"
    if POS_FILE.exists():
        pos_json = json.loads(POS_FILE.read_text(encoding="utf-8") or "{}")
        rows = []
        for t, p in pos_json.items():
            rows.append({
                "Ticker": t,
                "Status": p["status"],
                "Qty": p["qty"],
                "Entry": p["entry_price"],
                "TP": p["tp_price"],
                "SL": p["sl_price"],
                "Exit": p.get("exit_price"),
                "PnL%": p.get("pnl_pct"),
                "Opened": p["opened_at"],
                "Closed": p.get("closed_at"),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=380)
        else:
            st.warning("No positions yet.")

