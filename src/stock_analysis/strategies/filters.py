from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np

@dataclass
class OpeningBellFilterConfig:
    min_gap_pct: float = 0.5          # פער פתיחה מינימלי לעוצמה (%)
    min_rvol: float = 1.2             # נפח יחסי מינימלי
    require_vwap_above: bool = False   # פתיחה מעל VWAP
    orb_minutes: int = 15             # ORB: דקות ראשונות
    confirm_break_minutes: int = 45   # עד כמה מהר צריך לעבור את ה-ORB High
    min_dollar_vol_m: float = 1.0     # $Volume בדקות הראשונות (מ’)
    min_close_above_open_body: float = 0.25  # חוזק גוף: (Close-Open)/(High-Low) בנר הפתיחה
    min_rs_30m: float = 0.0           # Relative Strength מול benchmark ב-30 הדקות הראשונות (%)

def _safe_float(x) -> Optional[float]:
    try:
        f = float(x)
        if np.isfinite(f):
            return f
    except Exception:
        pass
    return None

def compute_relative_volume(df: pd.DataFrame, lookback: int = 50) -> Optional[float]:
    if "Volume" not in df.columns or df.empty:
        return None
    try:
        avg = float(df["Volume"].tail(lookback).mean())
        last = float(df["Volume"].iloc[-1])
        return last / avg if avg > 0 else None
    except Exception:
        return None

def compute_vwap(series_close: pd.Series, series_volume: pd.Series) -> pd.Series | None:
    if series_close.empty or series_volume.empty:
        return None
    pv = (series_close * series_volume).cumsum()
    vv = series_volume.cumsum().replace(0, pd.NA)
    return pv / vv

def compute_atr_5m(df: pd.DataFrame, lookback: int = 14) -> Optional[float]:
    req = {"High", "Low", "Close"}
    if not req.issubset(df.columns) or len(df) < lookback + 2:
        return None
    high, low, close_prev = df["High"], df["Low"], df["Close"].shift(1)
    tr = pd.concat([(high - low).abs(),
                    (high - close_prev).abs(),
                    (low - close_prev).abs()], axis=1).max(axis=1)
    atr = tr.rolling(lookback).mean().iloc[-1]
    return _safe_float(atr)

def candle_body_strength(row) -> Optional[float]:
    # (Close-Open)/(High-Low) – כמה הגוף דומיננטי בנר
    try:
        rng = float(row["High"] - row["Low"])
        return float((row["Close"] - row["Open"]) / rng) if rng > 0 else None
    except Exception:
        return None

def dollar_volume(row) -> Optional[float]:
    try:
        return float(row["Close"] * row["Volume"]) / 1_000_000.0
    except Exception:
        return None

def opening_range(df_today: pd.DataFrame, minutes: int) -> tuple[float, float]:
    head = df_today.iloc[: max(1, int(minutes * 60 // 300))]  # 300 שניות = 5 דק’; המרה בקירוב
    return float(head["High"].max()), float(head["Low"].min())

def first_idx_today(df_today: pd.DataFrame):
    return df_today.index[0] if not df_today.empty else None

def relative_strength_30m(df_sym: pd.DataFrame, df_bench: pd.DataFrame) -> Optional[float]:
    """שינוי % של הסימבול פחות שינוי % של בנצ'מרק ב-~30 דקות ראשונות של היום."""
    def _ret_30m(df):
        if df.empty:
            return None
        idx0 = df.index[0]
        bar_30 = min(len(df) - 1, 6)   # ~30min על 5m => 6 נרות
        p0 = _safe_float(df["Close"].iloc[0])
        p1 = _safe_float(df["Close"].iloc[bar_30])
        return ((p1 / p0 - 1.0) * 100.0) if p0 and p1 else None
    r1 = _ret_30m(df_sym)
    r2 = _ret_30m(df_bench)
    if r1 is None or r2 is None:
        return None
    return float(r1 - r2)

# Presets להגדרות OpeningBell+
def presets_for_openingbell(preset: str) -> OpeningBellFilterConfig:
    """
    מחזיר קונפיגורציה מוכנה לפי preset:
    - Loose   : קריטריונים רכים (יותר סיגנלים)
    - Default : ברירת מחדל מאוזנת
    - Strict  : קריטריונים קשיחים (פחות רעש)
    """
    p = (preset or "Default").lower()
    if p == "loose":
        return OpeningBellFilterConfig(
            orb_minutes=30, confirm_break_minutes=60,
            min_gap_pct=0.3, min_rvol=1.1, require_vwap_above=False,
            min_dollar_vol_m=0.8, min_close_above_open_body=0.15,
            min_rs_30m=-0.2,
        )
    if p == "strict":
        return OpeningBellFilterConfig(
            orb_minutes=30, confirm_break_minutes=45,
            min_gap_pct=0.8, min_rvol=1.5, require_vwap_above=True,
            min_dollar_vol_m=2.0, min_close_above_open_body=0.30,
            min_rs_30m=0.3,
        )
    # Default
    return OpeningBellFilterConfig(
        orb_minutes=30, confirm_break_minutes=45,
        min_gap_pct=0.5, min_rvol=1.2, require_vwap_above=True,
        min_dollar_vol_m=1.0, min_close_above_open_body=0.25,
        min_rs_30m=0.0,
    )
