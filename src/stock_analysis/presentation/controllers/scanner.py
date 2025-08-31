from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
import streamlit as st
import pandas as pd

from stock_utils import load_sp500_symbols, load_nasdaq_symbols
from stock_analysis.ml.periodic_models import predict_success as predict_success_all
from stock_analysis.presentation.ui.components.table import render_table
from stock_analysis.presentation.ui.components.expanders import render_stock_expander
from stock_analysis.presentation.plotting import plot_intraday_openingbell
from stock_analysis.strategies import registry as strategy_registry

from stock_analysis.services.risk import build_trade_plan
from stock_analysis.domain.entities import StrategySignal
from stock_analysis.infrastructure.persistent.sqlite_repo import SignalRepository

from stock_analysis.domain.decision import evaluate_openingbell_row
from stock_analysis.presentation.ui.components.decision import render_decision_card

# --------- עזר: תיוג איכות ---------
def classify_quality(q: float | None) -> str:
    if q is None:
        return "Watch"
    q = float(q)
    if q >= 80:
        return "A"
    if q >= 60:
        return "B"
    return "Watch"


class ScannerController:
    def __init__(self, screener) -> None:
        self.screener = screener
        self.signal_repo = SignalRepository("signals.db")

    # ========= Cached universes (Daily/Intraday) =========
    @st.cache_data(show_spinner=False)
    def _sp500_symbols(_self) -> List[str]:
        return load_sp500_symbols()

    @st.cache_data(show_spinner=False)
    def _nasdaq_symbols(_self) -> List[str]:
        return load_nasdaq_symbols()

    # ========= DAILY SCAN (כפי שהיה) =========
    def _scan(self, symbols: List[str], limit: int, workers: int) -> Tuple[pd.DataFrame, List[Dict]] | Tuple[None, None]:
        if not symbols:
            st.warning("לא נמצאו סימבולים לסריקה.")
            return None, None
        if limit > 0:
            symbols = symbols[:limit]

        workers = max(1, min(int(workers), 16))
        progress = st.progress(0.0)
        status = st.empty()

        results: List[Dict] = []
        total = len(symbols)
        done = 0

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(self.screener.analyze_daily, sym): sym for sym in symbols}
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    if res:
                        horizons = predict_success_all(res)
                        res["AI Success by Horizon (%)"] = horizons
                        res["AI 1d"] = horizons.get("1d")
                        res["AI 1mo"] = horizons.get("1mo")
                        res["AI 1y"] = horizons.get("1y")
                        results.append(res)
                except Exception:
                    pass
                done += 1
                progress.progress(done / total)
                status.write(f"Analyzed {done}/{total}")

        progress.empty(); status.empty()

        if not results:
            st.warning("לא התקבלו תוצאות (ייתכן שרובן מחוץ לטווח המחיר בסיידבר).")
            return None, None

        df = pd.DataFrame([{
            "Symbol": r.get("Symbol"),
            "Name": r.get("Name"),
            "Price (USD)": r.get("Price (USD)"),
            "P/E Ratio": r.get("P/E Ratio"),
            "EPS": r.get("EPS"),
            "Profit Margin (%)": r.get("Profit Margin (%)"),
            "Beta": r.get("Beta"),
            "Sector": r.get("Sector"),
            "Free Cash Flow": r.get("Free Cash Flow"),
            "Revenue Growth (%)": r.get("Revenue Growth (%)"),
            "MA20 > MA200": bool(r.get("MA20 > MA200")),
            "MA50 > MA200": bool(r.get("MA50 > MA200")),
            "RSI": r.get("RSI"),
            "MACD Positive": bool(r.get("MACD Positive")),
            "MACD Value": r.get("MACD Value"),
            "Volume Ratio": r.get("Volume Ratio"),
            "Volume Status": r.get("Volume Status"),
            "Sentiment Score": r.get("Sentiment Score"),
            "Business Checklist": r.get("Business Checklist"),
            "Smart Score": r.get("Smart Score"),
            "Forecast": r.get("Forecast"),
            "AI 1d": r.get("AI 1d"),
            "AI 1mo": r.get("AI 1mo"),
            "AI 1y": r.get("AI 1y"),
        } for r in results])

        df = df.sort_values(by=["AI 1mo", "Smart Score", "Price (USD)"],
                            ascending=[False, False, True], na_position="last").reset_index(drop=True)
        return df, results

    def run_sp500(self, limit: int, workers: int):
        syms = self._sp500_symbols()
        return self._scan(syms, limit, workers)

    def run_nasdaq(self, limit: int, workers: int):
        syms = self._nasdaq_symbols()
        return self._scan(syms, limit, workers)

    # ========= Filters + sector options (Daily) =========
    @staticmethod
    def apply_filters(df: pd.DataFrame, sector: str, min_score: int, min_ai: float, ai_col: str) -> pd.DataFrame:
        out = df.copy()
        if sector != "הצג הכל":
            out = out[out["Sector"] == sector]
        if min_score > 0:
            out = out[out["Smart Score"] >= min_score]
        if min_ai > 0:
            out = out[out[ai_col].fillna(0) >= min_ai]
        return out.sort_values(by=[ai_col, "Smart Score", "Price (USD)"],
                               ascending=[False, False, True], na_position="last").reset_index(drop=True)

    @staticmethod
    def patch_sector_options(df: pd.DataFrame) -> None:
        """מעדכן את רשימת הסקטורים עבור ה-selectbox שבסיידבר, בלי ליצור וידג'ט נוסף."""
        sectors = ["הצג הכל"] + sorted(list(set(df["Sector"].dropna().astype(str).tolist())))
        st.session_state["sector_options"] = sectors
        current = st.session_state.get("sector_dynamic", "הצג הכל")
        if current not in sectors:
            st.session_state["sector_dynamic"] = "הצג הכל"

    def render_results(self, df: pd.DataFrame, results: List[Dict],
                       sector: str, min_smart: int, min_ai: float, ai_label: str) -> None:
        self.patch_sector_options(df)

        ai_map = {"יומי": "AI 1d", "חודשי (מחיר)": "AI 1mo", "שנתי": "AI 1y"}
        ai_col = ai_map[ai_label]
        filtered = self.apply_filters(
            df,
            st.session_state.get("sector_dynamic", "הצג הכל"),
            min_smart,
            float(min_ai),
            ai_col,
        )

        render_table(filtered.drop(columns=["Business Checklist"], errors="ignore"))
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ הורד CSV", data=csv, file_name="scan_results.csv", mime="text/csv")

        top_n = min(10, len(filtered))
        st.markdown("---")
        for i in range(top_n):
            sym = filtered.iloc[i]["Symbol"]
            match = next((r for r in results if r.get("Symbol") == sym), None)
            if match:
                render_stock_expander(match)

    # ========= BULK INTRADAY STRATEGY SCAN =========
    def scan_strategy_universe(
        self,
        strategy_name: str,
        symbols: List[str],
        limit: int,
        workers: int,
        only_buy: bool = True,
        min_quality: int = 0,
        allow_late_reclaim: bool = True,
    ) -> Tuple[pd.DataFrame, List[Dict]] | Tuple[None, None]:

        if not symbols:
            st.warning("לא נמצאו סימבולים לסריקה.")
            return None, None
        if limit > 0:
            symbols = symbols[:limit]

        try:
            strat = strategy_registry.get(strategy_name)
        except KeyError:
            st.error(f"Strategy not found: {strategy_name}")
            return None, None

        workers = max(1, min(int(workers), 16))
        progress = st.progress(0.0)
        status = st.empty()

        results_rows: List[Dict] = []
        raw_for_charts: List[Dict] = []
        total = len(symbols)
        done = 0

        dp = self.screener.data_provider
        period = getattr(self.screener.cfg, "intraday_period", "30d")
        interval = getattr(self.screener.cfg, "intraday_interval", "5m")

        # Late reclaim detector
        try:
            from stock_analysis.strategies.openingbell_plus import detect_late_reclaim
        except Exception:
            detect_late_reclaim = None  # fallback

        def _process(sym: str) -> Optional[Dict]:
            try:
                df = strat.run(sym, dp, period=period, interval=interval)
                if df is None or df.empty or ("Open" not in df.columns):
                    return None
                if "is_opening" not in df.columns or not df["is_opening"].any():
                    return None

                open_idx = df.index[df["is_opening"]][0]
                pos = list(df.index).index(open_idx)
                prev_close = float(df.iloc[pos - 1]["Close"]) if pos > 0 else None

                open_price = float(df.loc[open_idx, "Open"]) if pd.notna(df.loc[open_idx, "Open"]) else None
                sma20 = float(df.loc[open_idx, "SMA20"]) if ("SMA20" in df.columns and pd.notna(df.loc[open_idx, "SMA20"])) else None
                sma200 = float(df.loc[open_idx, "SMA200"]) if ("SMA200" in df.columns and pd.notna(df.loc[open_idx, "SMA200"])) else None
                signal = df.loc[open_idx, "signal"] if "signal" in df.columns else None
                reason = df.loc[open_idx, "signal_reason"] if "signal_reason" in df.columns else ""

                # --- נתונים שמגיעים מהאסטרטגיה (OpeningBell+) דרך attrs ---
                gap = df.attrs.get("gap_pct")
                rvol = df.attrs.get("rvol_open")
                rs30 = df.attrs.get("rs_30m")
                vwap_ok = df.attrs.get("vwap_ok")
                orh = df.attrs.get("orh_break")
                atr = df.attrs.get("atr_5m")   # לשימוש בתכנית המסחר

                # --- Quality score ---
                def _nz(x, d=0.0):
                    try:
                        return float(x)
                    except Exception:
                        return d

                quality = (
                    0.35 * max(0.0, _nz(gap)) +
                    0.35 * max(0.0, _nz(rvol) - 1.0) * 100 / 2 +
                    0.20 * max(0.0, _nz(rs30)) +
                    5.0  * (1.0 if vwap_ok else 0.0) +
                    5.0  * (1.0 if orh else 0.0)
                )
                tier = classify_quality(quality)

                # סינון לפי איכות
                if min_quality and (quality is None or quality < min_quality):
                    return None

                # רק BUY? אפשרות ל-Late Reclaim
                if only_buy and str(signal).upper() != "BUY":
                    if allow_late_reclaim and detect_late_reclaim is not None:
                        try:
                            if detect_late_reclaim(df, open_idx, window_min=90):
                                signal = "BUY"
                                reason = (reason + " | " if reason else "") + "LateReclaim"
                            else:
                                return None
                        except Exception:
                            return None
                    else:
                        return None

                # --- תכנית מסחר (אם יש ATR) ---
                plan = build_trade_plan(
                    sym, open_price, atr,
                    atr_mult_stop=1.2, rr_ratio=2.0, risk_budget_usd=100.0
                )

                # --- שמירה ל-DB (יומן) ---
                try:
                    sig = StrategySignal(
                        symbol=sym, strategy=strategy_name, open_time=str(pd.to_datetime(open_idx)),
                        open_price=open_price, prev_close=prev_close,
                        gap_pct=gap, rvol=rvol, vwap_ok=vwap_ok,
                        sma20=sma20, sma200=sma200, reason=reason, decision=str(signal).upper()
                    )
                    self.signal_repo.save(sig)
                except Exception:
                    pass

                delta_pct = None
                if open_price is not None and prev_close is not None and prev_close != 0:
                    delta_pct = (open_price / prev_close - 1.0) * 100.0
                
                row = {
                    "Symbol": sym,
                    "Signal": signal,
                    "Open Time": str(pd.to_datetime(open_idx)),
                    "Open": open_price,
                    "Prev Close": prev_close,
                    "Δ Open vs PrevClose (%)": round(delta_pct, 3) if delta_pct is not None else None,
                    "SMA20": sma20,
                    "SMA200": sma200,
                    "SMA20 > SMA200": (sma20 is not None and sma200 is not None and sma20 > sma200),
                    "Gap%": gap,
                    "RVOL": rvol,
                    "VWAP_OK": vwap_ok,
                    "Stop": plan.stop if plan else None,
                    "Target": plan.target if plan else None,
                    "Shares": plan.shares if plan else 0,
                    "Reason": reason,
                    "Quality Score": round(quality, 2),
                    "Setup": tier,
                    "_df": df,  # לגרף
                }
                return row
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_process, sym): sym for sym in symbols}
            for fut in as_completed(futures):
                row = fut.result()
                if row:
                    raw_for_charts.append(row)
                    results_rows.append({k: v for k, v in row.items() if k != "_df"})
                done += 1
                progress.progress(done / total)
                status.write(f"Scanned {done}/{total}")

        progress.empty(); status.empty()

        if not results_rows:
            st.warning("לא נמצאו סיגנלים (יתכן שהכול HOLD/אין נר פתיחה תקף).")
            return None, None

        df_out = pd.DataFrame(results_rows)
        df_out["Signal_ord"] = df_out["Signal"].apply(lambda s: 0 if str(s).upper() == "BUY" else 1)
        df_out["Tier_ord"] = df_out["Setup"].map({"A": 0, "B": 1, "Watch": 2})
        df_out = df_out.sort_values(
            by=["Signal_ord", "Tier_ord", "Quality Score", "Δ Open vs PrevClose (%)"],
            ascending=[True, True, False, False],
            na_position="last",
        ).drop(columns=["Signal_ord", "Tier_ord"]).reset_index(drop=True)

        return df_out, raw_for_charts

    def run_strategy_sp500(self, strategy_name: str, limit: int, workers: int,
                           only_buy: bool = True, min_quality: int = 0, allow_late_reclaim: bool = True):
        syms = self._sp500_symbols()
        return self.scan_strategy_universe(strategy_name, syms, limit, workers, only_buy, min_quality, allow_late_reclaim)

    def run_strategy_nasdaq(self, strategy_name: str, limit: int, workers: int,
                            only_buy: bool = True, min_quality: int = 0, allow_late_reclaim: bool = True):
        syms = self._nasdaq_symbols()
        return self.scan_strategy_universe(strategy_name, syms, limit, workers, only_buy, min_quality, allow_late_reclaim)

    def render_strategy_results(self, df: pd.DataFrame, rows: List[Dict], top_charts: int = 5, strategy_name: str = "Strategy") -> None:
        """מציג טבלה של הסיגנלים וגרפים עבור ה-Top N."""
        st.markdown(f"### ⚡ תוצאות סריקת אסטרטגיה ({strategy_name})")

        # סטייל לפי תיוג
        def _row_style(_):
            colors = []
            for t in df["Setup"]:
                if t == "A":
                    colors.append("background-color:#124c2f")
                elif t == "B":
                    colors.append("background-color:#3a3550")
                else:
                    colors.append("background-color:#343434")
            return [colors]

        styled = df.style.set_table_styles(
            [{"selector": "th", "props": [("background-color", "#202020")]}]
        ).apply(lambda _: _row_style(_)[0], subset=["Setup"])

        st.dataframe(styled, use_container_width=True, height=420)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ הורד CSV (אסטרטגיה)", data=csv, file_name="strategy_signals.csv", mime="text/csv")

        if top_charts and top_charts > 0:
            st.markdown("---")
            st.subheader(f"גרפים 5m — Top {min(top_charts, len(df))}")
            top = min(top_charts, len(df))
            for i in range(top):
                sym = df.iloc[i]["Symbol"]
                row = next((r for r in rows if r["Symbol"] == sym), None)
                if not row:
                    continue

                # גרף
                fig = plot_intraday_openingbell(row["_df"], sym)
                st.plotly_chart(fig, use_container_width=True)

                # החלטה
                plan = {"stop": row.get("Stop"), "target": row.get("Target"), "shares": row.get("Shares")}
                dec = evaluate_openingbell_row(row, plan)
                render_decision_card(dec)
                st.markdown("---")
