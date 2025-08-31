import numpy as np
import pandas as pd
import pytz
from datetime import datetime
from .base_strategy import BaseStrategy

US_EASTERN = pytz.timezone("US/Eastern")


def _as_series_close(df: pd.DataFrame) -> pd.Series:
    close = df["Close"]
    # אם זה DataFrame (למשל MultiIndex/עמודות כפולות) – קח את העמודה הראשונה
    if isinstance(close, pd.DataFrame):
        if close.shape[1] >= 1:
            close = close.iloc[:, 0]
        else:
            return pd.Series(dtype=float, index=df.index)
    return close.squeeze()


class OpeningBellStrategy(BaseStrategy):
    def evaluate_opening_bar(self, df5: pd.DataFrame):
        if df5.empty:
            return False, "empty df"

        # הבטח TZ
        if df5.index.tz is None:
            df5.index = df5.index.tz_localize("UTC").tz_convert(US_EASTERN)
        else:
            df5.index = df5.index.tz_convert(US_EASTERN)

        df5 = df5.copy()
        df5["date"] = df5.index.tz_convert(US_EASTERN).date
        today = datetime.now(US_EASTERN).date()

        today_df = df5[df5["date"] == today]
        prev_df  = df5[df5["date"] <  today]
        if today_df.empty:
            return False, "no today bars yet"
        if prev_df.empty:
            return False, "no previous day bars"

        open_bar = today_df.iloc[0]
        prev_day_last = prev_df[prev_df["date"] == prev_df["date"].max()].iloc[-1]

        # --- NEW: rolling על Series אמיתית ---
        close_ser = _as_series_close(df5)
        sma20_ser = close_ser.rolling(window=20, min_periods=20).mean()
        sma200_ser = close_ser.rolling(window=200, min_periods=200).mean()
        # שיוך בטוח לעמודות (להימנע מקונפליקט צורות)
        df5 = df5.assign(SMA20=sma20_ser.values, SMA200=sma200_ser.values)
        # --------------------------------------

        ts_open = today_df.index[0]
        hist_to_open = df5.loc[:ts_open]
        if hist_to_open.empty:
            return False, "no history up to open"

        row_at_open = hist_to_open.iloc[-1]

        # המרות נקיות ל-scalar
        def _as_scalar(v):
            if isinstance(v, pd.Series):
                v = v.iloc[-1] if len(v) else np.nan
            if hasattr(v, "item"):
                try:
                    v = v.item()
                except Exception:
                    pass
            try:
                return float(v)
            except Exception:
                return float("nan")

        sma20 = _as_scalar(row_at_open["SMA20"])
        sma200 = _as_scalar(row_at_open["SMA200"])
        if pd.isna(sma20) or pd.isna(sma200):
            return False, "not enough history for SMA"

        open_high = _as_scalar(open_bar["High"])
        prev_close = _as_scalar(prev_day_last["Close"])

        cond1 = sma20 > sma200
        cond2 = open_high > prev_close

        if cond1 and cond2:
            reason = (
                f"SMA20({sma20:.2f})>SMA200({sma200:.2f}) & "
                f"OpenHigh({open_high:.2f})>PrevClose({prev_close:.2f})"
            )
            return True, reason

        return False, (
            f"no-signal (SMA20={sma20:.2f}, SMA200={sma200:.2f}, "
            f"openHigh={open_high:.2f}, prevClose={prev_close:.2f})"
        )
