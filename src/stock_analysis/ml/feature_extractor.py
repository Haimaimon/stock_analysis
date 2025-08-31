from __future__ import annotations
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Optional, List, Dict

import pandas as pd

# Clean-arch: עובדים מול DataProvider, ברירת מחדל YFinance
from stock_analysis.domain.interfaces import DataProvider
from stock_analysis.infrastructure.data_providers.yfinance_provider import YFinanceProvider

# שכבת התאימות – שומר על אותה לוגיקה של חישובי אינדיקטורים
from stock_utils import compute_rsi, compute_macd, analyze_volume


@dataclass
class FeatureExtractor:
    data_provider: DataProvider = YFinanceProvider()

    def extract(self, ticker: str) -> Optional[Dict]:
        """
        ממיר את ML/feature_extractor.extract_features הישן למחלקה מודולרית.
        מחזיר dict עם אותם מפתחות בדיוק.
        """
        try:
            info = self.data_provider.info(ticker)

            # Daily frames לפי התקופה
            hist_1d  = self.data_provider.history(ticker, period="2d",  interval="1d")
            hist_1mo = self.data_provider.history(ticker, period="1mo", interval="1d")
            hist_1y  = self.data_provider.history(ticker, period="1y",  interval="1d")

            if hist_1y.empty or len(hist_1y) < 200:
                return None

            price_now = info.get("currentPrice", None)
            if not price_now:
                return None

            # ממוצעים נעים + אינדיקטורים (לפי הלוגיקה שלך)
            ma20  = hist_1y["Close"].rolling(window=20).mean().iloc[-1]
            ma50  = hist_1y["Close"].rolling(window=50).mean().iloc[-1]
            ma200 = hist_1y["Close"].rolling(window=200).mean().iloc[-1]
            rsi   = compute_rsi(hist_1y["Close"])
            macd  = compute_macd(hist_1y["Close"])
            volume_ratio, _ = analyze_volume(hist_1y)

            # Success labels
            success_1d = 0
            success_1mo = 0
            success_1y = 0

            try:
                price_yesterday = hist_1d["Close"].iloc[0]
                if price_now > price_yesterday * 1.03:
                    success_1d = 1
            except Exception:
                pass

            try:
                price_month_ago = hist_1mo["Close"].iloc[0]
                if price_now > price_month_ago * 1.05:
                    success_1mo = 1
            except Exception:
                pass

            try:
                price_year_ago = hist_1y["Close"].iloc[0]
                if price_now > price_year_ago * 1.15:
                    success_1y = 1
            except Exception:
                pass

            return {
                "Ticker": ticker,
                "RSI": rsi,
                "MACD": macd,
                "MA20_gt_MA200": int(ma20 > ma200),
                "MA50_gt_MA200": int(ma50 > ma200),
                "PE_Ratio": info.get("trailingPE", 0),
                "EPS": info.get("trailingEps", 0),
                "ProfitMargin": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else 0,
                "RevenueGrowth": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else 0,
                "FreeCashFlow": info.get("freeCashflow", 0),
                "VolumeRatio": volume_ratio,
                "Sector": info.get("sector", "Other"),
                "Success_1d": success_1d,
                "Success_1mo": success_1mo,
                "Success_1y": success_1y,
            }
        except Exception as e:
            print(f"❌ Error in {ticker}: {e}")
            return None

    def batch(self, symbols: Iterable[str], max_threads: int = 5) -> pd.DataFrame:
        print(f"🚀 Extracting features for {len(list(symbols))} symbols...")
        results: List[Dict] = []
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {executor.submit(self.extract, sym): sym for sym in symbols}
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    results.append(r)
        df = pd.DataFrame(results)
        df.dropna(inplace=True)
        print(f"✅ Extracted features for {len(df)} stocks")
        return df


# --- פונקציות תאימות בשמות המקוריים ---

def extract_features(ticker: str):
    return FeatureExtractor().extract(ticker)

def batch_extract(symbols: Iterable[str], max_threads: int = 5) -> pd.DataFrame:
    return FeatureExtractor().batch(list(symbols), max_threads=max_threads)
