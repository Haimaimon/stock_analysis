import streamlit as st
from stock_analysis.domain.decision import Decision

def render_decision_card(dec: Decision) -> None:
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1: st.metric("Quality", dec.score)
    with col2: st.metric("Go/No-Go", "GO ✅" if dec.go else "NO-GO ❌")
    with col3: st.metric("Stop", f"{dec.stop:.3f}" if dec.stop else "—")
    with col4: st.metric("Target", f"{dec.target:.3f}" if dec.target else "—")

    st.write("**Reasons**")
    for r in dec.reasons: st.write(r)
    st.info(f"**Entry plan:** {dec.entry_hint}\n\n**Shares:** {dec.shares}")
