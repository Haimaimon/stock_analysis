from __future__ import annotations
import streamlit as st
import pandas as pd

def style_bulk_df(df: pd.DataFrame):
    """Styler לטבלת התוצאות. בלי type-hint כדי למנוע בעיות גרסאות pandas."""
    def _neg_red(v):
        try:
            return "background-color: rgba(255, 0, 0, 0.18)" if float(v) < 0 else ""
        except Exception:
            return ""
    def _macd_color(v):
        try:
            return "background-color: rgba(0, 255, 0, 0.12)" if float(v) > 0 else "background-color: rgba(255, 0, 0, 0.12)"
        except Exception:
            return ""
    sty = (df.style
             .applymap(_neg_red, subset=["EPS", "Profit Margin (%)"])
             .applymap(_macd_color, subset=["MACD Value"])
             .format({"Price (USD)": "{:.2f}",
                      "P/E Ratio": "{:.2f}",
                      "EPS": "{:.2f}",
                      "Profit Margin (%)": "{:.2f}",
                      "Revenue Growth (%)": "{:.1f}",
                      "RSI": "{:.2f}",
                      "MACD Value": "{:.4f}",
                      "Volume Ratio": "{:.2f}",
                      "Sentiment Score": "{:.2f}",
                      "AI 1d": "{:.2f}",
                      "AI 1mo": "{:.2f}",
                      "AI 1y": "{:.2f}",
                      "Smart Score": "{:.0f}"})
         )
    return sty

def render_table(df: pd.DataFrame) -> None:
    st.dataframe(style_bulk_df(df), use_container_width=True, height=420)
