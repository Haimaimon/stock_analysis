from __future__ import annotations
from typing import List, Tuple
import streamlit as st
import pandas as pd
from stock_analysis.presentation.plotting import plot_candlestick
from stock_analysis.ml.feature_explainer import explain_features

def _targeted_insights(stock: dict) -> List[Tuple[str, str]]:
    rsi = float(stock.get("RSI", 50) or 50)
    macd = float(stock.get("MACD Value", 0) or 0)
    sent = float(stock.get("Sentiment Score", 0) or 0)
    rev = float(stock.get("Revenue Growth (%)", 0) or 0)
    pm  = float(stock.get("Profit Margin (%)", 0) or 0)
    ma20gt200 = bool(stock.get("MA20 > MA200"))
    ma50gt200 = bool(stock.get("MA50 > MA200"))

    out: List[Tuple[str, str]] = []
    out.append(("Technical View",
                f"RSI={rsi:.1f} ({'Overbought' if rsi>70 else 'Oversold' if rsi<30 else 'Neutral'}), "
                f"MACD={'+' if macd>0 else '-'}, Trend "
                f"{'Up' if (ma20gt200 and ma50gt200) else 'Mixed'}."))

    out.append(("Fundamentals",
                f"Revenue Growth {rev:.1f}%, Profit Margin {pm:.1f}%."))

    if sent > 0.2:
        out.append(("Catalysts", "Positive news sentiment lately."))
    elif sent < -0.2:
        out.append(("Risks", "Negative sentiment—watch headlines."))

    out.append(("Strategy", "Entry: MA20 pullbacks; stop < MA50; targets at swing highs."))
    return out

def render_stock_expander(stock: dict) -> None:
    symbol = stock.get("Symbol")
    smart = stock.get("Smart Score", 0)
    with st.expander(f"📌 {symbol} – {smart} :ציון חכם", expanded=False):
        st.caption(f"**תחזית**: {stock.get('Forecast', '—')}")
        st.caption(f"**מדד סנטימנט**: {stock.get('Sentiment Score', 0):.2f}")

        st.markdown("**AI Success by Horizon (%)**")
        st.json(stock.get("AI Success by Horizon (%)", {}))

        hist_df: pd.DataFrame = stock.get("History")
        if isinstance(hist_df, pd.DataFrame) and not hist_df.empty:
            st.plotly_chart(plot_candlestick(hist_df, symbol), use_container_width=True)

        st.markdown("### ניתוח עסקי:")
        checklist = stock.get("Business Checklist", {})
        if checklist:
            biz_df = pd.DataFrame.from_dict(checklist, orient="index", columns=["Value"]).reset_index()
            biz_df.columns = ["Parameter", "Value"]
            st.dataframe(biz_df, use_container_width=True, hide_index=True)
        else:
            st.info("אין נתוני צ'ק-ליסט זמינים.")

        st.markdown("### ניתוח פיצ'רים:")
        rows = explain_features(stock)
        exp_df = pd.DataFrame(rows)
        st.dataframe(exp_df, use_container_width=True, hide_index=True)

        insights = _targeted_insights(stock)
        st.markdown("### ניתוח ממוקד:")
        for cat, desc in insights:
            st.write(f"- **{cat}**: {desc}")

        st.markdown(f"[🛒 BUY {symbol} on Yahoo Finance](https://finance.yahoo.com/quote/{symbol})")
