from __future__ import annotations
from datetime import timedelta
import pandas as pd
from stock_analysis.domain.interfaces import DataProvider

class OpeningBellStrategy:
    """
    Opening Bell (5m):
    1) SMA20 > SMA200
    2) פתיחת היום > סגירת הנר האחרון של אתמול
    מציב signal רק על נר הפתיחה של הסשן הנוכחי: BUY/HOLD (לעולם לא None).
    מוסיף:
      - is_opening: True על נר הפתיחה של היום
      - signal_reason: טקסט לתיאור התנאים (ל-tooltip)
    """
    name = "OpeningBell"
    exchange_tz = "America/New_York"

    def run(
        self,
        symbol: str,
        data_provider: DataProvider,
        period: str = "5d",
        interval: str = "5m",
    ) -> pd.DataFrame:
        df = data_provider.history(symbol, period=period, interval=interval)
        if df is None or df.empty or len(df) < 220:
            return pd.DataFrame()  # לא מספיק נתונים ל-SMA200

        df = df.copy()

        # הבטחת tz-aware -> NY
        try:
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            df_ny = df.tz_convert(self.exchange_tz)
        except Exception:
            df_ny = df.copy()
            df_ny.index = df_ny.index.tz_localize(None)

        # ממוצעים נעים
        df["SMA20"]  = df["Close"].rolling(window=20,  min_periods=20).mean()
        df["SMA200"] = df["Close"].rolling(window=200, min_periods=200).mean()

        # תאריכי סשן (לפי NY)
        if df.index.tz is not None:
            session_dates = df.index.tz_convert(self.exchange_tz).date
        else:
            session_dates = pd.to_datetime(df.index).date
        df["session_date"] = session_dates

        sessions = sorted(df["session_date"].unique())
        df["signal"] = None
        df["is_opening"] = False
        df["signal_reason"] = None

        if len(sessions) == 0:
            return df.drop(columns=["session_date"])

        current_session = sessions[-1]
        prev_session = sessions[-2] if len(sessions) >= 2 else None

        today_mask = df["session_date"] == current_session
        today_data = df.loc[today_mask]
        if today_data.empty:
            return df.drop(columns=["session_date"])

        open_idx = today_data.index[0]
        df.loc[open_idx, "is_opening"] = True

        # סגירת הסשן הקודם
        last_y_close = None
        if prev_session is not None:
            y_mask = df["session_date"] == prev_session
            y_closes = df.loc[y_mask, "Close"]
            if not y_closes.empty:
                last_y_close = float(y_closes.iloc[-1])

        sma20 = df.loc[open_idx, "SMA20"]
        sma200 = df.loc[open_idx, "SMA200"]
        open_price = df.loc[open_idx, "Open"]

        # טקסט תנאים (גם אם חסר חלק מהמידע)
        def fmt(x, nd=3):
            try: return f"{float(x):.{nd}f}"
            except Exception: return "N/A"

        reason = (
            f"SMA20 {fmt(sma20)} {'>' if (pd.notna(sma20) and pd.notna(sma200) and float(sma20)>float(sma200)) else '<=' if pd.notna(sma20) and pd.notna(sma200) else '?'} "
            f"SMA200 {fmt(sma200)} | "
            f"Open {fmt(open_price)} {'>' if (pd.notna(open_price) and (last_y_close is not None) and float(open_price)>last_y_close) else '<=' if (pd.notna(open_price) and (last_y_close is not None)) else '?'} "
            f"PrevClose {fmt(last_y_close)}"
        )
        df.loc[open_idx, "signal_reason"] = reason

        if pd.notna(sma20) and pd.notna(sma200) and pd.notna(open_price) and (last_y_close is not None):
            cond = (float(sma20) > float(sma200)) and (float(open_price) > last_y_close)
            df.loc[open_idx, "signal"] = "BUY" if cond else "HOLD"
        else:
            df.loc[open_idx, "signal"] = "HOLD"

        return df.drop(columns=["session_date"])
