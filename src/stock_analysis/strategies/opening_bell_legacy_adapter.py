# src/stock_analysis/strategies/opening_bell_legacy_adapter.py
from __future__ import annotations
import pandas as pd
from typing import Optional, Dict, Any
from stock_analysis.domain.interfaces import DataProvider
from stock_analysis.strategies.opening_bell import OpeningBell

def check_opening_bell_conditions(symbol: str, data_provider: DataProvider) -> Optional[Dict[str, Any]]:
    """
    תאימות לאחור לפונקציה הישנה.
    משתמש ב-DataProvider כדי להוריד 5d @ 5m, מריץ את ה-Strategy, ומחזיר dict אם יש איתות.
    """
    # 5 ימים ב-5 דקות (דומה למימוש הקודם שלך)
    df = data_provider.history(symbol, period="5d", interval="5m")
    if df.empty or len(df) < 100:
        return None

    strat = OpeningBell()
    out = strat.generate_signals(df)

    # אם נוצר איתות בנר הראשון של היום – נחזיר פרטים כמו בקוד הישן
    last_date = out["date"].max() if "date" in out else out.index.date.max()
    today_df = out[out["date"] == last_date] if "date" in out else out[out.index.date == last_date]
    if today_df.empty:
        return None

    first_idx = today_df.index[0]
    if bool(out.loc[first_idx, strat.signal_col]):
        # חישוב ערכי ה-SMA ונגזרות
        yesterday = sorted(out["date"].unique())[-2]
        prev_df = out[out["date"] == yesterday]
        return {
            "symbol": symbol,
            "open_price": float(out.loc[first_idx, "Open"]),
            "prev_close": float(prev_df.iloc[-1]["Close"]),
            "sma20": float(out.loc[first_idx, "SMA20"]),
            "sma200": float(out.loc[first_idx, "SMA200"]),
        }
    return None
