from __future__ import annotations
import streamlit as st
import pandas as pd

from stock_analysis.presentation.ui.state import UIState
from stock_analysis.presentation.ui.components.metrics import render_kpis
from stock_analysis.ml.periodic_models import predict_success as predict_success_all
from stock_analysis.presentation.plotting import plot_candlestick
from stock_analysis.ml.feature_explainer import explain_features

class DailyController:
    def __init__(self, screener) -> None:
        self.screener = screener

    def analyze(self, symbol: str) -> dict | None:
        with st.spinner("Analyzing daily data..."):
            return self.screener.analyze_daily(symbol)

    def render(self, res: dict, col_chart_area) -> None:
        # נשמור את התוצאה כדי שהסבר ישרוד rerun
        UIState.set_last_daily(res)

        st.subheader(f"🔎 {res['Symbol']} — {res.get('Name','')}")
        render_kpis(res)
        st.info(res.get("Forecast", "—"))

        horizons = predict_success_all(res)
        st.markdown("**AI Success by Horizon (%)**")
        st.json(horizons)

        # הכפתור מדליק דגל בצורה בטוחה ל-rerun
        st.button("🧠 Explain features",
                  key=f"explain_{res['Symbol']}",
                  on_click=UIState.enable_explain)

        # גרף
        hist_df: pd.DataFrame = res["History"]
        with col_chart_area:
            st.plotly_chart(
                plot_candlestick(hist_df, res["Symbol"]),
                use_container_width=True
            )

        # Checklist
        st.subheader("📋 Business Checklist")
        checklist = res.get("Business Checklist", {})
        st.table(pd.DataFrame.from_dict(checklist, orient="index", columns=["Value"]))

    def render_explain_if_needed(self) -> None:
        """מציג הסבר פיצ'רים אם הדגל דולק ותוצאה קיימת ב-session."""
        if not UIState.is_explain_on():
            return

        _res = UIState.get_last_daily()
        if _res is None:
            st.info("אין ניתוח אחרון להצגה. הרץ ניתוח יומי ואז לחץ על Explain features.")
            UIState.disable_explain()
            return

        with st.spinner("Building feature explanation..."):
            df_exp = pd.DataFrame(explain_features(_res))

        st.subheader("הסבר פיצ'רים (תרומה לניקוד)")
        st.table(df_exp)

        csv = df_exp.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Download explanation CSV",
            data=csv,
            file_name=f"{_res['Symbol']}_explanation.csv",
            mime="text/csv",
        )

        if st.button("סגור הסבר"):
            UIState.disable_explain()
