from __future__ import annotations
import asyncio
import pandas as pd
import pytz
import yfinance as yf
import logging

from ...domain.ports import MarketDataFeed

log = logging.getLogger(__name__)
US_EASTERN = pytz.timezone("US/Eastern")

class YFinanceFeed(MarketDataFeed):
    async def get_5m_history(self, ticker: str, days: int = 10) -> pd.DataFrame:
        loop = asyncio.get_running_loop()
        df = await loop.run_in_executor(None, self._fetch_single, ticker, days)
        return df

    def _fetch_single(self, ticker: str, days: int) -> pd.DataFrame:
        log.debug("yfinance.history | %s | %sd 5m", ticker, days)
        t = yf.Ticker(ticker)
        df = t.history(period=f"{days}d", interval="5m", prepost=False, actions=False, auto_adjust=False)

        if df.empty:
            log.warning("yfinance empty DF | %s", ticker)
            return df

        # הבטח טיים-זון
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert(US_EASTERN)
        else:
            df.index = df.index.tz_convert(US_EASTERN)

        # השם של yfinance כבר "Open/High/Low/Close/Volume" בקייס הזה; נעשה עותק נקי
        cols = ["Open", "High", "Low", "Close", "Volume"]
        df = df[cols].copy()

        log.debug("yfinance processed | %s | rows=%d | first=%s | last=%s | closeHead=%.4f",
                  ticker, len(df), df.index[0], df.index[-1], float(df["Close"].iloc[0]))
        return df
