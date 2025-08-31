from __future__ import annotations
import pandas as pd
import numpy as np
from stock_analysis.strategies.filters import (
    OpeningBellFilterConfig, compute_relative_volume, compute_vwap,
    compute_atr_5m, candle_body_strength, dollar_volume,
    opening_range, first_idx_today, relative_strength_30m
)

# בחר בנצ'מרק לשוק כולו (אפשר לשפר ל-ETF סקטוריאלי בהמשך)
BENCH_SYMBOL = "SPY"

class OpeningBellPlus:
    name = "OpeningBell+"

    def __init__(self, filters: OpeningBellFilterConfig | None = None) -> None:
        # מאפשר להזרים preset מבחוץ (app.py -> presets_for_openingbell)
        self.filters = filters

    def run(self, symbol: str, data_provider, period: str = "5d", interval: str = "5m") -> pd.DataFrame | None:
        # נתונים לסימבול
        df = data_provider.history(symbol, period=period, interval=interval)
        if df is None or df.empty or not {"Open","High","Low","Close","Volume"}.issubset(df.columns):
            return None
        df = df.copy()

        # נתוני בנצ'מרק
        bench = data_provider.history(BENCH_SYMBOL, period=period, interval=interval)
        if bench is None or bench.empty:
            bench = pd.DataFrame(index=df.index, data={"Close": np.nan, "Volume": np.nan})

        # פירוק ליום הנוכחי
        today = pd.to_datetime(df.index[-1]).date()
        df_today = df.loc[pd.to_datetime(df.index).date == today].copy()
        if df_today.empty:
            return None

        # VWAP, ATR
        vwap_all = compute_vwap(df["Close"], df["Volume"])
        atr_5m = compute_atr_5m(df, lookback=14)

        # ORB
        cfg = self.filters or OpeningBellFilterConfig()
        orb_high, orb_low = opening_range(df_today, minutes=cfg.orb_minutes)
        open_idx = first_idx_today(df_today)
        if open_idx is None:
            return None

        # מאפייני נר פתיחה
        open_row = df.loc[open_idx]
        body_power = candle_body_strength(open_row)
        dvol_m = dollar_volume(open_row)

        # Prev close
        try:
            pos = list(df.index).index(open_idx)
            prev_close = float(df.iloc[pos - 1]["Close"]) if pos > 0 else None
        except Exception:
            prev_close = None

        gap_pct = None
        if prev_close and prev_close != 0:
            gap_pct = (float(open_row["Open"]) / prev_close - 1.0) * 100.0

        # RVOL עד הפתיחה
        rvol_open = compute_relative_volume(df[df.index <= open_idx], lookback=50)

        # VWAP OK
        vwap_open = float(vwap_all.loc[open_idx]) if vwap_all is not None and open_idx in vwap_all.index else None
        vwap_ok = (float(open_row["Open"]) >= vwap_open) if (vwap_open is not None) else None

        # Relative Strength 30m
        bench_today = bench.loc[pd.to_datetime(bench.index).date == today].copy()
        rs_30m = relative_strength_30m(df_today, bench_today)

        # אישורים
        confirms: list[tuple[str,bool]] = []
        def ok(cond, tag):
            confirms.append((tag, bool(cond)))
            return bool(cond)

        passed = True
        if gap_pct is not None:
            passed &= ok(gap_pct >= cfg.min_gap_pct, f"Gap>={cfg.min_gap_pct}%")
        if rvol_open is not None:
            passed &= ok(rvol_open >= cfg.min_rvol, f"RVOL>={cfg.min_rvol}")
        if vwap_ok is not None and cfg.require_vwap_above:
            passed &= ok(vwap_ok, "Open>=VWAP")
        if dvol_m is not None:
            passed &= ok(dvol_m >= cfg.min_dollar_vol_m, f"$Vol>={cfg.min_dollar_vol_m}M")
        if body_power is not None:
            passed &= ok(body_power >= cfg.min_close_above_open_body, f"BodyPower>={cfg.min_close_above_open_body}")
        if rs_30m is not None:
            passed &= ok(rs_30m >= cfg.min_rs_30m, f"RS30m>={cfg.min_rs_30m}%")

        # אישור ORB: עד window צריך להיות close מעל ORH
        confirm_bars = min(len(df_today)-1, max(1, cfg.confirm_break_minutes // 5))
        orh_break = False
        if confirm_bars > 0:
            orh_break = bool((df_today["Close"].iloc[:confirm_bars] > orb_high).any())
            passed &= ok(orh_break, f"Break ORH<= {cfg.confirm_break_minutes}m")

        # החזרת DF עשיר לתצוגה
        out = df.copy()
        out["SMA20"] = out["Close"].rolling(4).mean()      # 4*5m ~ 20m
        out["SMA200"] = out["Close"].rolling(40).mean()    # 40*5m ~ 200m
        out["vwap"] = vwap_all                             # לשימוש ב-Late Reclaim
        out["orh"]  = np.nan
        out.loc[df_today.index, "orh"] = orb_high

        out["is_opening"] = False
        out.loc[open_idx, "is_opening"] = True
        out["signal"] = "BUY" if passed else "HOLD"
        out["signal_reason"] = "; ".join([t for t, ok_ in confirms if ok_]) if passed \
                               else "Failed: " + "; ".join([t for t, ok_ in confirms if not ok_])

        # מאפיינים לעיבוד/תצוגה בהמשך
        out.attrs["open_idx"]        = open_idx
        out.attrs["signal_at_open"]  = out.loc[open_idx, "signal"]
        out.attrs["reason_at_open"]  = out.loc[open_idx, "signal_reason"]
        out.attrs["gap_pct"]         = gap_pct
        out.attrs["rvol_open"]       = rvol_open
        out.attrs["vwap_ok"]         = vwap_ok
        out.attrs["dollar_vol_m"]    = dvol_m
        out.attrs["atr_5m"]          = atr_5m
        out.attrs["rs_30m"]          = rs_30m
        out.attrs["orb_high"]        = orb_high
        out.attrs["orh_break"]       = orh_break

        return out


# --------- Late reclaim detector (פונקציית עזר חיצונית) ---------
def detect_late_reclaim(df: pd.DataFrame, open_idx, window_min: int = 90) -> bool:
    """
    מחפש התאוששות לאחר הפתיחה:
    - Close חוזר מעל VWAP (או SMA20 כחלופה) + פריצת ORH בתקופה של window_min דקות מהפתיחה.
    """
    try:
        start_pos = list(df.index).index(open_idx)
    except Exception:
        return False

    bars = max(1, window_min // 5)
    end_pos = min(len(df), start_pos + bars)
    win = df.iloc[start_pos:end_pos].copy()
    if win.empty:
        return False

    # תנאי 1: reclaim מעל vwap (fallback ל-SMA20 אם אין)
    if "vwap" in win.columns and win["vwap"].notna().any():
        above_line = (win["Close"] > win["vwap"]).rolling(3).sum() >= 2
    else:
        sma = win.get("SMA20")
        if sma is None or sma.isna().all():
            return False
        above_line = (win["Close"] > sma).rolling(3).sum() >= 2

    # תנאי 2: פריצה מעל ORH (מהעמודה או מה-attrs)
    orh = None
    if "orh" in win.columns:
        ser = win["orh"].ffill()           # תיקון ל-FutureWarning (במקום fillna(method="ffill"))
        orh = float(ser.dropna().iloc[0]) if ser.notna().any() else None
    if orh is None:
        orh = df.attrs.get("orb_high")

    orh_ok = bool(orh is not None and (win["Close"] > float(orh)).any())

    return bool(above_line.any() and orh_ok)
