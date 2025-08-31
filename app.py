# app.py — Presentation shell (uses modular controllers/components)
import streamlit as st
import pandas as pd

from stock_analysis.presentation.app_services import build_screener
from stock_analysis.presentation.ui.components.forms import sidebar
from stock_analysis.presentation.ui.state import UIState
from stock_analysis.presentation.controllers.daily import DailyController
from stock_analysis.presentation.controllers.scanner import ScannerController
from stock_analysis.presentation.plotting import plot_intraday_openingbell
from stock_analysis.services.watchlist import WatchlistService

# Presets + רישום אסטרטגיות
from stock_analysis.strategies.filters import presets_for_openingbell
from stock_analysis.strategies.openingbell_plus import OpeningBellPlus
from stock_analysis.strategies import registry as strategy_registry

# רענון מחירי S&P 500 + תאריך עדכון אחרון
from stock_analysis.infrastructure.data.sp500 import (
    refresh_sp500_prices,
    get_last_update_date,
)

@st.cache_resource
def _get_watchlist():
    return WatchlistService(".watchlist.json")

watchlist = _get_watchlist()

st.set_page_config(page_title="Smart Stock Screener", layout="wide")
st.title("📈 Smart Stock Screener – ניתוח טכני, פנדמנטלי, גרף, סנטימנט + תחזיות")

# >>> חשוב: לאתחל session_state בכל rerun
UIState.init()

# ---- UI forms (sidebar) ----
ui, scan = sidebar()

# ===== OpeningBell+ Tuning (Preset / Quality / Late Reclaim) =====
with st.sidebar.expander("⚙️ OpeningBell+ Tuning", expanded=False):
    preset = st.selectbox("Preset", ["Loose", "Default", "Strict"],
                          index=["Loose","Default","Strict"].index(st.session_state.get("ob_preset", "Default")),
                          key="ob_preset_select")
    if st.button("Apply preset", use_container_width=True, key="apply_preset"):
        fcfg = presets_for_openingbell(preset)
        # רושם/מעדכן את OpeningBell+ עם הפילטרים החדשים
        strategy_registry.register("OpeningBell+", OpeningBellPlus(filters=fcfg))
        st.success(f"Preset applied: {preset}")
        st.session_state["ob_preset"] = preset
        st.rerun()

    # סף איכות מינימלי לסיגנל
    min_quality = st.slider("Min Quality (OpeningBell+)", 0, 120,
                            value=int(st.session_state.get("min_quality", 0)),
                            key="min_quality")
    # Late Reclaim – לאפשר BUY מאוחר אם הייתה התאוששות מעל VWAP+ORH
    allow_late_reclaim = st.toggle("Allow Late Reclaim (BUY after recovery)",
                                   value=bool(st.session_state.get("allow_late_reclaim", True)),
                                   key="allow_late_reclaim")

with st.sidebar:
    st.markdown("---")
    st.subheader("👀 Watchlist")

    # הצגה/הוספה של הסימבול הנוכחי
    st.text_input("סימבול נוכחי", value=ui.symbol or "", disabled=True, key="curr_symbol_display")
    add_disabled = not bool(ui.symbol)
    if st.button("➕ הוסף ל-Watchlist", disabled=add_disabled, key="watch_add_btn"):
        new_list = watchlist.add(ui.symbol.upper())
        st.success(f"נוסף: {ui.symbol.upper()}  •  סה״כ: {len(new_list)}")

    # הצגת רשימה (טקסטואלית, בלי וידג׳טים כפולים)
    wl_syms = watchlist.load()
    st.caption(f"📌 ברשימה: {len(wl_syms)} סימבולים")
    if wl_syms:
        st.write(", ".join(wl_syms[:80]))  # הדגמה קצרה

        # כפתור סריקה לאסטרטגיה על כל ה-Watchlist
        if st.button("⚡ סרוק Watchlist (OpeningBell)", key="watch_scan_btn"):
            st.session_state["do_watch_scan"] = True

# ---- Build services (DI) ----
@st.cache_resource
def _get_screener(min_p: float, max_p: float):
    return build_screener(min_p, max_p)

screener = _get_screener(ui.min_price, ui.max_price)
daily = DailyController(screener)
scanner = ScannerController(screener)

with st.sidebar.expander("📦 Universe Data", expanded=False):
    st.caption(f"עדכון אחרון לקובץ S&P 500: {get_last_update_date()}")
    if st.button("🔄 רענן S&P 500 (מחירים)", use_container_width=True):
        with st.spinner("מרענן מחירי S&P 500..."):
            refresh_sp500_prices()  # כותב sp500_prices.csv חדש
        # לנקות cache של רשימת הסימבולים כדי שייטען מהקובץ המעודכן
        try:
            scanner._sp500_symbols.clear()   # כי _sp500_symbols היא @st.cache_data
        except Exception:
            pass
        st.success("✅ עודכן! תריץ סריקה מחדש כדי לראות את המחירים המעודכנים.")
        st.rerun()

# ---- Layout columns ----
col1, col2 = st.columns([1.2, 1])

# ---- Single symbol daily analysis ----
if ui.run_daily and ui.symbol:
    res = daily.analyze(ui.symbol)
    if res is None:
        st.error("לא נמצאו נתונים/לא עומד בתנאים (היסטוריה/טווח מחיר).")
    else:
        with col1:
            daily.render(res, col_chart_area=col1)
        with col2:
            pass  # daily.render כבר מציג שם Checklist

# הסבר פיצ'רים — תמיד מחוץ לבלוקים כדי לשרוד rerun
daily.render_explain_if_needed()

# ---- Intraday strategy (optional) ----
if ui.run_intraday and ui.symbol:
    with st.spinner(f"Running {ui.selected_strategy} on 5m data..."):
        out = screener.analyze_intraday_with_strategy(ui.symbol, strategy_name=ui.selected_strategy)
    if out is None:
        st.error("אין מספיק נתוני אינטראדיי או אירעה שגיאה.")
    else:
        st.subheader(f"⚡ Strategy Signals — {ui.selected_strategy}")
        show_cols = [c for c in ["Open", "Close", "SMA20", "SMA200", "signal"] if c in out.columns]
        st.plotly_chart(plot_intraday_openingbell(out, ui.symbol), use_container_width=True)
        st.dataframe(out.tail(50)[show_cols], use_container_width=True)

# ---- Bulk scans ----
bulk_df = None
bulk_results = None

if scan.run_sp500:
    with st.spinner("Scanning S&P 500..."):
        bulk_df, bulk_results = scanner.run_sp500(limit=scan.max_to_scan, workers=scan.workers)

if scan.run_nasdaq:
    with st.spinner("Scanning NASDAQ..."):
        bulk_df, bulk_results = scanner.run_nasdaq(limit=scan.max_to_scan, workers=scan.workers)

# ---- Bulk Strategy scans ----
if scan.run_strategy_sp500:
    with st.spinner("Running OpeningBell on S&P 500..."):
        strat_df, strat_rows = scanner.run_strategy_sp500(
            strategy_name=ui.selected_strategy,
            limit=scan.max_to_scan,
            workers=scan.workers,
            only_buy=scan.only_buy_signals,
            min_quality=st.session_state.get("min_quality", 0),
            allow_late_reclaim=st.session_state.get("allow_late_reclaim", True),
        )
    if strat_df is not None and strat_rows is not None:
        scanner.render_strategy_results(strat_df, strat_rows, top_charts=scan.top_charts, strategy_name=ui.selected_strategy)

if scan.run_strategy_nasdaq:
    with st.spinner("Running OpeningBell on NASDAQ..."):
        strat_df, strat_rows = scanner.run_strategy_nasdaq(
            strategy_name=ui.selected_strategy,
            limit=scan.max_to_scan,
            workers=scan.workers,
            only_buy=scan.only_buy_signals,
            min_quality=st.session_state.get("min_quality", 0),
            allow_late_reclaim=st.session_state.get("allow_late_reclaim", True),
        )
    if strat_df is not None and strat_rows is not None:
        scanner.render_strategy_results(strat_df, strat_rows, top_charts=scan.top_charts, strategy_name=ui.selected_strategy)

# ---- Strategy scan on Watchlist ----
if st.session_state.get("do_watch_scan"):
    st.session_state["do_watch_scan"] = False
    sym_list = watchlist.load()
    if not sym_list:
        st.info("ה-Watchlist ריק.")
    else:
        with st.spinner("Running OpeningBell on Watchlist..."):
            strat_df, strat_rows = scanner.scan_strategy_universe(
                strategy_name=ui.selected_strategy,          # לרוב "OpeningBell" או "OpeningBell+"
                symbols=sym_list,
                limit=scan.max_to_scan,
                workers=scan.workers,
                only_buy=scan.only_buy_signals,
                min_quality=st.session_state.get("min_quality", 0),
                allow_late_reclaim=st.session_state.get("allow_late_reclaim", True),
            )
        if strat_df is not None and strat_rows is not None:
            scanner.render_strategy_results(strat_df, strat_rows, top_charts=scan.top_charts, strategy_name=ui.selected_strategy)
        else:
            st.info("לא נמצאו סיגנלים ב-Watchlist.")

# ---- Render bulk daily results table ----
if bulk_df is not None and bulk_results is not None:
    st.markdown("### 🟩 טבלת מניות מעניינות:")
    scanner.render_results(
        bulk_df, bulk_results,
        sector=ui.sector_pick, min_smart=ui.min_smart,
        min_ai=ui.min_ai, ai_label=ui.ai_horizon_label
    )
