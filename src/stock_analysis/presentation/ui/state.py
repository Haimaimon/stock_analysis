from __future__ import annotations
from typing import Any, Optional
import streamlit as st

class UIState:
    """עטיפה ממושמעת ל-session_state (מונעת מפתחות אקראיים)."""

    LAST_DAILY = "last_daily_result"
    SHOW_EXPLAIN = "show_explain"

    @classmethod
    def init(cls) -> None:
        """אתחול דגלים כבר בתחילת האפליקציה כדי לשרוד rerun."""
        st.session_state.setdefault(cls.LAST_DAILY, None)
        st.session_state.setdefault(cls.SHOW_EXPLAIN, False)

    @classmethod
    def get_last_daily(cls) -> Optional[dict]:
        return st.session_state.get(cls.LAST_DAILY)

    @classmethod
    def set_last_daily(cls, res: dict) -> None:
        st.session_state[cls.LAST_DAILY] = res

    @classmethod
    def enable_explain(cls) -> None:
        st.session_state[cls.SHOW_EXPLAIN] = True

    @classmethod
    def disable_explain(cls) -> None:
        st.session_state[cls.SHOW_EXPLAIN] = False

    @classmethod
    def is_explain_on(cls) -> bool:
        return bool(st.session_state.get(cls.SHOW_EXPLAIN, False))

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        st.session_state[key] = value
