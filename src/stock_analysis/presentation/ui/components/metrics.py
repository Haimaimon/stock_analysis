from __future__ import annotations
import streamlit as st

def render_kpis(res: dict) -> None:
    cols = st.columns(6)
    cols[0].metric("Price (USD)", res.get("Price (USD)", "-"))
    cols[1].metric("Smart Score", res.get("Smart Score", "-"))
    cols[2].metric("RSI", res.get("RSI", "-"))
    cols[3].metric("MACD+", "Yes" if res.get("MACD Positive") else "No")
    cols[4].metric("Sentiment", f"{res.get('Sentiment Score', 0):.2f}")
    cols[5].metric("Sector", res.get("Sector", "-"))
