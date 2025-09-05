from __future__ import annotations
import os, time, random, threading, asyncio, logging
from typing import Optional

import pandas as pd
import pytz
import yfinance as yf

from ...domain.ports import MarketDataFeed

log = logging.getLogger(__name__)
US_EASTERN = pytz.timezone("US/Eastern")

# ===== הגדרות שניתנות לשליטה דרך ENV =====
YF_RATE_PER_MIN   = int(os.getenv("YF_RATE_PER_MIN", "90"))   # קצב בקשות/דקה
YF_MAX_RETRIES    = int(os.getenv("YF_MAX_RETRIES", "3"))     # כמה ניסיונות חוזרים
YF_BASE_BACKOFF   = float(os.getenv("YF_BASE_BACKOFF", "1.5"))# שניות (אקספוננציאלי)
YF_MAX_BACKOFF    = float(os.getenv("YF_MAX_BACKOFF", "10"))  # תקרת השהייה בין ניסיונות
YF_ALLOW_PREPOST  = os.getenv("YF_ALLOW_PREPOST", "false").lower() == "true"

# ===== Rate Limiter בטוח ל-Threadים =====
class RateLimiter:
    """Token bucket פשוט לשמירה על קצב yfinance."""
    def __init__(self, rate_per_minute: int = 60):
        self.capacity = float(rate_per_minute)
        self.tokens   = float(rate_per_minute)
        self.rate     = float(rate_per_minute) / 60.0
        self.last     = time.time()
        self.lock     = threading.Lock()

    def acquire(self):
        # נחזור עד שנקבל 'טוקן'
        while True:
            with self.lock:
                now = time.time()
                delta = now - self.last
                self.tokens = min(self.capacity, self.tokens + delta * self.rate)
                self.last = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                # צריך לחכות
                needed = (1.0 - self.tokens) / self.rate
            # מחוץ לנעילה
            time.sleep(needed + random.uniform(0, 0.25))

_limiter = RateLimiter(rate_per_minute=YF_RATE_PER_MIN)

def _with_backoff(callable_fn):
    """
    מפעיל פונקציה סינכרונית עם RateLimit + retry/backoff.
    מחזיר את הערך, או מעלה את החריגה בניסיון האחרון כדי שתירשם בלוג.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(YF_MAX_RETRIES + 1):
        try:
            _limiter.acquire()
            return callable_fn()
        except Exception as e:
            last_exc = e
            if attempt >= YF_MAX_RETRIES:
                break
            sleep = min(YF_BASE_BACKOFF * (2 ** attempt), YF_MAX_BACKOFF) + random.uniform(0, 0.5)
            log.warning("yfinance call failed (attempt %d/%d): %s | sleeping %.1fs",
                        attempt + 1, YF_MAX_RETRIES, e, sleep)
            time.sleep(sleep)
    # ניסיון אחרון נכשל – נרים שגיאה כדי שתתועד
    raise last_exc if last_exc else RuntimeError("yfinance call failed")

class YFinanceFeed(MarketDataFeed):
    async def get_5m_history(self, ticker: str, days: int = 10) -> pd.DataFrame:
        loop = asyncio.get_running_loop()
        # מפעיל את הפונקציה הסינכרונית ב-executor כדי לא לחסום את event loop
        df = await loop.run_in_executor(None, self._fetch_single_safe, ticker, days)
        return df

    def _fetch_single_safe(self, ticker: str, days: int) -> pd.DataFrame:
        """עטיפה בטוחה: rate-limit + backoff + תיקוני טיים-זון/עמודות."""
        ticker = (ticker or "").strip().upper()
        if not ticker:
            return pd.DataFrame()

        def _do_fetch():
            t = yf.Ticker(ticker)
            return t.history(
                period=f"{int(days)}d",
                interval="5m",
                prepost=YF_ALLOW_PREPOST,   # ברירת המחדל False – RTH בלבד
                actions=False,
                auto_adjust=False,
            )

        try:
            df = _with_backoff(_do_fetch)
        except Exception as e:
            log.error("yfinance.history failed | %s | %sd 5m | %s", ticker, days, e)
            return pd.DataFrame()

        if df is None or df.empty:
            log.info("yfinance empty DF | %s", ticker)
            return pd.DataFrame()

        # טיים-זון ל-US/Eastern
        try:
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC").tz_convert(US_EASTERN)
            else:
                df.index = df.index.tz_convert(US_EASTERN)
        except Exception:
            # לפעמים אינדקס DatetimeIndex "naive" או בעייתי – ננסה לאנוס
            try:
                df.index = pd.to_datetime(df.index, utc=True).tz_convert(US_EASTERN)
            except Exception:
                pass  # נשאיר כמו שזה – טוב מספיק לבדיקות אחרות

        # בחר עמודות סטנדרטיות אם קיימות
        wanted = ["Open", "High", "Low", "Close", "Volume"]
        cols = [c for c in wanted if c in df.columns]
        if not cols:
            # אם העמודות לא סטנדרטיות (נדיר), נחזיר כמו שהוא
            return df
        df = df[cols].copy()

        # לוג עדין בלבד אם יש נתונים
        try:
            log.debug("yfinance processed | %s | rows=%d | first=%s | last=%s | closeHead=%.4f",
                      ticker, len(df), df.index[0], df.index[-1], float(df["Close"].iloc[0]))
        except Exception:
            pass
        return df
