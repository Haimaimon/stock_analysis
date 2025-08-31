# src/stock_analysis/finnhub_news.py
from __future__ import annotations

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import requests

# ===== נסיונות טעינה "רכים" של מנועי סנטימנט =====
_HAS_HF = True
try:
    from transformers import pipeline as hf_pipeline  # כבד; לא חובה ב-Free tier
except Exception:
    _HAS_HF = False
    hf_pipeline = None  # type: ignore

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _HAS_VADER = True
except Exception:
    _HAS_VADER = False
    SentimentIntensityAnalyzer = None  # type: ignore


@dataclass
class NewsItem:
    headline: str
    summary: Optional[str] = None
    url: Optional[str] = None


class FinnhubNewsAnalyzer:
    """
    מנתח חדשות מ-Finnhub עם מנוע סנטימנט אופציונלי:
    - אם יש transformers + ביקשת להשתמש (use_hf=True): pipeline("sentiment-analysis")
    - אחרת: VADER (קל ומהיר)
    - ואם גם VADER לא קיים: fallback פשוט על בסיס מילות מפתח
    """

    def __init__(self, api_key: str, use_hf: bool = False, request_timeout: int = 12):
        self.api_key = api_key
        self.request_timeout = int(request_timeout)

        self._mode = "none"
        self._hf = None
        self._vader = None

        if use_hf and _HAS_HF:
            # מודל קליל יחסית; חותכים טקסט ל-512 תווים בעת הקריאה
            self._hf = hf_pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
            )
            self._mode = "hf"
        elif _HAS_VADER:
            self._vader = SentimentIntensityAnalyzer()
            self._mode = "vader"
        else:
            self._mode = "rule"  # מילות מפתח בסיסיות

    # ----------- Data fetching -----------

    def fetch_news(self, symbol: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """מביא חדשות 7 ימים אחורה (ברירת מחדל) עבור סימבול מ-Finnhub."""
        symbol = (symbol or "").upper().strip()
        if not symbol:
            return []

        from_date = (datetime.utcnow() - timedelta(days=int(days_back))).strftime("%Y-%m-%d")
        to_date = datetime.utcnow().strftime("%Y-%m-%d")

        url = "https://finnhub.io/api/v1/company-news"
        params = {"symbol": symbol, "from": from_date, "to": to_date, "token": self.api_key}

        try:
            r = requests.get(url, params=params, timeout=self.request_timeout)
            r.raise_for_status()
            data = r.json()
            # ודא שמחזירים רשימה
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"❌ שגיאה בשליפת חדשות מ-Finnhub עבור {symbol}: {e}")
            return []

    # ----------- Sentiment scoring -----------

    def _score_text(self, text: str) -> float:
        """
        מחזיר ציון סנטימנט בתחום [-1..1]:
        חיובי ~ +1, שלילי ~ -1, ניטרלי ~ 0
        """
        text = (text or "").strip()
        if not text:
            return 0.0

        if self._mode == "hf" and self._hf is not None:
            out = self._hf(text[:512])[0]  # {'label': 'POSITIVE'|'NEGATIVE', 'score': float}
            return float(out["score"] if out["label"] == "POSITIVE" else -out["score"])

        if self._mode == "vader" and self._vader is not None:
            s = self._vader.polarity_scores(text)  # {'compound': [-1..1], ...}
            return float(s.get("compound", 0.0))

        # Fallback כללי (מאוד פשוט) אם אין שום מנוע מותקן
        POS_WORDS = ("beat estimates", "beats", "surge", "upgrade", "bullish",
                     "record", "strong", "growth", "profit", "top", "positive")
        NEG_WORDS = ("miss estimates", "misses", "plunge", "downgrade", "bearish",
                     "loss", "weak", "lawsuit", "cut", "negative")

        low = text.lower()
        score = 0.0
        score += sum(1 for w in POS_WORDS if w in low) * 0.2
        score -= sum(1 for w in NEG_WORDS if w in low) * 0.2
        return max(-1.0, min(1.0, score))

    def analyze_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        מקבל את הפלט הגולמי של Finnhub (רשימת dicts) ומחזיר סיכום:
        Total / Positive / Negative / Neutral / Sentiment Score
        """
        pos = neg = neu = 0
        total = 0

        for art in articles or []:
            title = art.get("headline", "") or ""
            summary = art.get("summary", "") or ""
            text = f"{title}. {summary}".strip()
            if not text:
                continue

            s = self._score_text(text)
            total += 1

            # סיווג לפי סף סטנדרטי (VADER): >0.05=חיובי, <-0.05=שלילי, אחרת ניטרלי
            if s > 0.05:
                pos += 1
            elif s < -0.05:
                neg += 1
            else:
                neu += 1

        score = round(((pos - neg) / total), 2) if total > 0 else 0.0
        return {
            "Engine": self._mode,         # 'hf' | 'vader' | 'rule'
            "Total Articles": total,
            "Positive": pos,
            "Negative": neg,
            "Neutral": neu,
            "Sentiment Score": score,     # בטווח בערך [-1..1]
        }

    # ----------- Convenience -----------

    def run_full_analysis(self, symbol: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        news = self.fetch_news(symbol)
        sentiment = self.analyze_sentiment(news)
        return sentiment, news
