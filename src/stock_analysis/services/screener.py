# src/stock_analysis/services/screener.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Any, Optional
import pandas as pd

from stock_analysis.domain.interfaces import DataProvider, SentimentAnalyzer, BusinessChecklist, SuccessPredictor
from stock_analysis.services.scoring import ScoringPolicy
from stock_analysis.features.pipeline import Pipeline

# שימוש בשכבת התאימות כדי לא לשבור כלום
from stock_utils import generate_forecast  # compat layer (ממפה ל-utils/forecast)
from stock_analysis.strategies import registry as strategy_registry

@dataclass
class ScreenerConfig:
    min_price: float = 8.0
    max_price: float = 14.0
    history_period: str = "1y"
    history_interval: str = "1d"
    intraday_period: str = "5d"
    intraday_interval: str = "5m"

@dataclass
class Screener:
    data_provider: DataProvider
    sentiment_analyzer: SentimentAnalyzer
    business_checklist: BusinessChecklist
    success_predictor: SuccessPredictor

    daily_pipeline: Optional[Pipeline] = None
    scoring: ScoringPolicy = field(default_factory=ScoringPolicy)
    cfg: ScreenerConfig = field(default_factory=ScreenerConfig)


    # ---------- DAILY ANALYZE (כמו stock_analysis_engine הישן) ----------
    def analyze_daily(self, symbol: str) -> dict | None:
        try:
            info = self.data_provider.info(symbol)
            hist = self.data_provider.history(symbol, period=self.cfg.history_period, interval=self.cfg.history_interval)

            if hist.empty or len(hist) < 200:
                print(f"⚠️ אין מספיק היסטוריית מחיר למניה {symbol}")
                return None

            price = self.data_provider.last_price(symbol)
            if not price:
                print(f"❌ אין מחיר נוכחי עבור {symbol}")
                return None
            if price < self.cfg.min_price or price > self.cfg.max_price:
                print(f"⛔ מחיר {price} לא בטווח: {self.cfg.min_price}–{self.cfg.max_price}")
                return None

            # הפעלת Pipeline אם סופק (מוסיף עמודות כמו RSI/MACD/SMA וכו')
            df = hist.copy()
            df.columns = [c.title() for c in df.columns]  # Ensure ['Open','High','Low','Close','Volume']
            if self.daily_pipeline:
                df = self.daily_pipeline.run(df)

            # שליפות ערכים אחרונים לפי שמות עמודות הצפויים
            ma20  = df["Close"].rolling(20).mean().iloc[-1]
            ma50  = df["Close"].rolling(50).mean().iloc[-1]
            ma200 = df["Close"].rolling(200).mean().iloc[-1]
            rsi_last = float(df.get("RSI", pd.Series([None])).iloc[-1]) if "RSI" in df else None
            macd_last = float(df.get("MACD Value", df.get("MACD", pd.Series([None]))).iloc[-1]) if (("MACD Value" in df) or ("MACD" in df)) else None
            # נפח – ייתכן שנוסף ע"י step או נחשב מהיסטוריה
            if "Volume Ratio" in df and "Volume Status" in df:
                volume_ratio = float(df["Volume Ratio"].iloc[-1])
                volume_status = str(df["Volume Status"].iloc[-1])
            else:
                # fallback חכם אם אין step נפח
                avg_volume = df["Volume"].mean()
                latest_volume = df["Volume"].iloc[-1]
                volume_ratio = round(latest_volume / avg_volume, 2) if avg_volume else 0.0
                volume_status = "High" if volume_ratio > 1.5 else "Normal"

            # סנטימנט
            sentiment_data, _ = self.sentiment_analyzer.run_full_analysis(symbol)
            sentiment_score = float(sentiment_data.get("Sentiment Score", 0.0))

            # צ'קליסט עסקי
            checklist = self.business_checklist(info, sentiment_score, symbol, self.sentiment_analyzer)

            stock: dict[str, Any] = {
                "Symbol": symbol,
                "Name": info.get("shortName", ""),
                "Price (USD)": round(price, 2),
                "P/E Ratio": info.get("trailingPE"),
                "EPS": info.get("trailingEps"),
                "Profit Margin (%)": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else None,
                "Beta": info.get("beta"),
                "Sector": info.get("sector"),
                "Free Cash Flow": info.get("freeCashflow"),
                "Revenue Growth (%)": info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else 0,
                "MA20 > MA200": bool(ma20 and ma200 and (ma20 > ma200)),
                "MA50 > MA200": bool(ma50 and ma200 and (ma50 > ma200)),
                "RSI": round(rsi_last, 2) if rsi_last is not None else None,
                "MACD Positive": (macd_last is not None and macd_last > 0),
                "MACD Value": macd_last,
                "Volume Ratio": volume_ratio,
                "Volume Status": volume_status,
                "Sentiment Score": sentiment_score,
                "History": df,  # שומר את ה-DF המעובד (כולל פיצ’רים) לשימוש ב-UI
                "Business Checklist": checklist,
            }

            stock["Smart Score"] = self.scoring.score(stock)
            stock["Forecast"] = generate_forecast(stock["Smart Score"], stock["Sentiment Score"])
            stock["AI Success Probability (%)"] = self.success_predictor.predict_success(stock)

            print("✅ ניקוד מפורט:", stock["Symbol"], stock["Smart Score"])
            return stock

        except Exception as e:
            print(f"❌ שגיאה בניתוח מניה {symbol}: {e}")
            return None

    # ---------- INTRADAY + STRATEGY (למשל OpeningBell) ----------
    def analyze_intraday_with_strategy(self, symbol: str, strategy_name: str) -> Optional[pd.DataFrame]:
        """מריץ אסטרטגיית אינטרדיי על נרות 5m (או לפי cfg)."""
        try:
            strat = strategy_registry.get(strategy_name)
        except KeyError:
            # שגיאת מפתח – לא נרשם ברג’יסטרי
            print(f"[Screener] Strategy not found: {strategy_name}")
            return None

        try:
            df = strat.run(
                symbol=symbol,
                data_provider=self.data_provider,
                period=self.cfg.intraday_period,
                interval=self.cfg.intraday_interval,
            )
            if df is None or df.empty:
                return None
            return df
        except Exception as e:
            print(f"❌ Error in strategy {strategy_name} for {symbol}: {e}")
            return None
