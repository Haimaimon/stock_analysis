from __future__ import annotations
from datetime import datetime, time, timedelta
import pytz
import streamlit as st

IL = pytz.timezone("Asia/Jerusalem")

def next_open_dt(now_il: datetime) -> datetime:
    """החזרה של היעד הבא ל-16:30 היום, ואם עבר – 16:30 של מחר (לא מטפל בחגים/סופ"ש של וול-סטריט)."""
    target_today = now_il.replace(hour=16, minute=30, second=0, microsecond=0)
    if now_il <= target_today:
        return target_today
    return (target_today + timedelta(days=1))

def render_open_countdown() -> None:
    now_il = datetime.now(IL)
    target = next_open_dt(now_il)
    delta = target - now_il

    # רענון אוטומטי כל שנייה (אם קיים, אחרת נתן פallback)
    try:
        # Streamlit 1.18+: st.autorefresh
        st.autorefresh(interval=1000, key="open_countdown_refresh")
    except Exception:
        # Fallback קטן: לא קריטי אם אין — עדיין נראה את הספירה ידנית
        pass

    if delta.total_seconds() > 0:
        hrs, rem = divmod(int(delta.total_seconds()), 3600)
        mins, secs = divmod(rem, 60)

        st.markdown("### ⏳ Waiting for market open")
        st.write("**Target (Israel time):** 16:30")
        st.markdown(
            f"""
            <div style="font-size:2rem; font-weight:700; padding:8px 0;">
              {hrs:02d}:{mins:02d}:{secs:02d}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(min(1.0, (1.0 - delta.total_seconds() / (24*3600))))  # אינדיקציה כללית
    else:
        st.markdown("### ✅ Market is open")
        st.success("The strategy is live. Scanning 5-minute opening bar conditions…")
