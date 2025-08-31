from __future__ import annotations
from dataclasses import dataclass
import os
import streamlit as st
from stock_analysis.strategies import registry as strategy_registry

@dataclass
class UISettings:
    symbol: str
    min_price: float
    max_price: float
    sector_pick: str
    min_smart: int
    ai_horizon_label: str
    min_ai: float
    selected_strategy: str
    run_daily: bool
    run_intraday: bool

@dataclass
class ScanControls:
    max_to_scan: int
    workers: int
    run_sp500: bool
    run_nasdaq: bool
    # NEW: bulk intraday strategy controls
    run_strategy_sp500: bool
    run_strategy_nasdaq: bool
    only_buy_signals: bool
    top_charts: int

def sidebar() -> tuple[UISettings, ScanControls]:
    with st.sidebar:
        st.subheader("🧮 סינון לפי מחיר")
        symbol = st.text_input("Symbol", value="F").strip().upper()
        min_price = st.slider("מחיר מינימלי ($)", 1.0, 200.0, 8.0, 1.0)
        max_price = st.slider("מחיר מקסימלי ($)", 8.0, 500.0, 14.0, 1.0)

        # בתוך sidebar()
        st.markdown("### 🧠 סינון נוסף")

        # אתחול ברירת מחדל אם לא קיים
        st.session_state.setdefault("sector_dynamic", "הצג הכל")

        # קבלה של רשימת האפשרויות מה-Scanner (אם עוד לא נסרק – תהיינה אפשרויות ברירת מחדל)
        sector_options = st.session_state.get("sector_options", ["הצג הכל"])
        st.selectbox("בחר סקטור", options=sector_options, key="sector_dynamic")
      
        min_smart = st.slider("Smart Score מינימלי", 0, 100, 40, 5)
        ai_horizon_label = st.selectbox("בחר טווח זמן לסינון AI", ["יומי", "חודשי (מחיר)", "שנתי"], index=1)
        min_ai = st.slider("AI Success Probability מינימלי (%)", 0, 100, 0, 5)

        st.markdown("---")
        st.subheader("🧪 אסטרטגיית פתיחה")
        strategies = strategy_registry.available() or ["OpeningBell"]
        selected_strategy = st.selectbox("בחר אסטרטגיה (5m)", strategies, index=0)
        run_daily = st.button("🔎 ניתוח יומי (Symbol)")
        run_intraday = st.button("⚡ אסטרטגיית פתיחה")

        st.markdown("---")
        st.subheader("📦 סריקה מרובה (Bulk)")
        max_to_scan = st.number_input("כמות מקסימלית לסריקה", value=150, step=50, min_value=10)
        default_workers = min(8, max(2, (os.cpu_count() or 4) // 2))
        workers = st.slider("Parallel workers", 1, 16, default_workers)
        run_sp500 = st.button("⬇️ טען S&P 500")
        run_nasdaq = st.button("⬇️ טען NASDAQ")

        # --- חדש: סריקת אסטרטגיה אינטראדיי על יקום שלם ---
        st.markdown("---")
        st.subheader("⚡ סריקת אסטרטגיה (5m)")
        run_strategy_sp500 = st.button("⚡ OpeningBell על S&P 500")
        run_strategy_nasdaq = st.button("⚡ OpeningBell על NASDAQ")
        only_buy_signals = st.checkbox("הצג רק BUY", value=True)
        top_charts = st.slider("כמה גרפים להציג (Top N)", 0, 10, 5)

    ui = UISettings(
        symbol=symbol, min_price=min_price, max_price=max_price,
        sector_pick=st.session_state["sector_dynamic"],
        min_smart=min_smart, ai_horizon_label=ai_horizon_label,
        min_ai=min_ai, selected_strategy=selected_strategy,
        run_daily=run_daily, run_intraday=run_intraday,
    )
    scan = ScanControls(
        max_to_scan=int(max_to_scan),
        workers=int(workers),
        run_sp500=run_sp500,
        run_nasdaq=run_nasdaq,
        # NEW:
        run_strategy_sp500=run_strategy_sp500,
        run_strategy_nasdaq=run_strategy_nasdaq,
        only_buy_signals=only_buy_signals,
        top_charts=int(top_charts),
    )
    return ui, scan
