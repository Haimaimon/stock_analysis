# app.py – ראשי
import streamlit as st
import pandas as pd
import random
from datetime import datetime

from stock_utils import (
    fetch_symbols_with_price_range,
    refresh_sp500_prices,
    get_last_update_date,
    plot_candlestick,
)
from stock_analysis_modules import run_full_analysis
from finnhub_news import FinnhubNewsAnalyzer
from stock_analysis_engine import fetch_stock_data


# ========== הגדרות ראשוניות ==========
st.set_page_config(page_title="📊 Ultimate Stock Screener", layout="wide")
st.title("📊 Smart Stock Screener – ניתוח טכני, פונדמנטלי, גרף, סנטימנט + תחזית")


# ========== סרגל צד ==========
st.sidebar.markdown("## 🎯 סינון לפי מחיר")
min_price = st.sidebar.slider("מחיר מינימלי ($)", 1, 200, 8)
max_price = st.sidebar.slider("מחיר מקסימלי ($)", min_price, 500, 14)

# 🎯 פילטר לפי סקטור וציון חכם
st.sidebar.markdown("## 🧠 סינון נוסף")
selected_sector = st.sidebar.selectbox(
    "בחר סקטור",
    options=["הצג הכל", "Technology", "Healthcare", "Communication Services", "Consumer Cyclical", "Utilities"]
)

min_smart_score = st.sidebar.slider(
    "Smart Score מינימלי",
    min_value=0,
    max_value=100,
    value=40
)

st.sidebar.markdown("---")
st.sidebar.markdown("🔄 **עדכון מחירים**")
if st.sidebar.button("🔁 רענן נתוני מחירים (S&P 500)"):
    refresh_sp500_prices()
st.sidebar.markdown(f"🕒 `עודכן לאחרונה: {get_last_update_date()}`")


# ========== כפתור ניתוח ==========
if st.button("🔍 טען ונתח מניות עם ציון חכם"):
    with st.spinner("⏳ מנתח נתונים..."):
        analyzer = FinnhubNewsAnalyzer("cnnc531r01qq36n63pt0cnnc531r01qq36n63ptg")
        symbols = fetch_symbols_with_price_range(min_price, max_price)
        random.shuffle(symbols)

        stocks = []
        for symbol in symbols:
            print(f"🔄 בודק מניה: {symbol}")
            stock = fetch_stock_data(symbol, analyzer, min_price, max_price)
            if stock:
                print(f"✅ נמצאה מניה: {symbol}")
                stocks.append(stock)
                if len(stocks) >= 10:
                    break

        if not stocks:
            st.warning("😕 לא נמצאו מניות מתאימות.")
        else:
            # ✨ סינון לפי סקטור ו־Smart Score
            if selected_sector != "הצג הכל":
                stocks = [s for s in stocks if s.get("Sector") == selected_sector]
            stocks = [s for s in stocks if s.get("Smart Score", 0) >= min_smart_score]
            df = pd.DataFrame([{k: v for k, v in s.items() if k not in ["Ticker", "History"]} for s in stocks])
            st.success("📋 טבלת מניות עם ניתוח כולל:")
            st.dataframe(df, use_container_width=True)

            for stock in stocks:
                with st.expander(f"📌 ניתוח למניה: {stock['Symbol']} – ציון חכם: {stock['Smart Score']}"):
                    st.markdown(f"**🧠 תחזית חכמה:** {stock['Forecast']}")
                    st.markdown(f"**📰 ניקוד סנטימנט:** {stock['Sentiment Score']}")
                    st.plotly_chart(plot_candlestick(stock["History"], stock["Symbol"]), use_container_width=True)

                    st.markdown("### 🧾 ניתוח עסקי לפי צ'ק ליסט:")
                    checklist = run_full_analysis(stock["Ticker"].info, stock["Sentiment Score"])
                    checklist_df = pd.DataFrame(checklist.items(), columns=["Parameter", "Value"])
                    st.dataframe(checklist_df, use_container_width=True)
else:
    st.info("בחר טווח מחירים ולחץ על הכפתור כדי לטעון מניות.")
