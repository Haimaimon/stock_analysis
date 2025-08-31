# src/stock_analysis/services/scoring.py
from __future__ import annotations

class ScoringPolicy:
    """מחשב 'Smart Score' לפי הקריטריונים המקוריים שלך."""
    def score(self, stock: dict) -> int:
        score = 0
        rsi = stock.get("RSI", 100)
        if 30 <= rsi <= 50:
            score += 10
        if stock.get("MACD Positive"):
            score += 10
        if stock.get("MA20 > MA200"):
            score += 15
        if stock.get("MA50 > MA200"):
            score += 10
        if stock.get("Revenue Growth (%)", 0) > 10:
            score += 15
        if stock.get("Profit Margin (%)", 0) > 5:
            score += 10
        if stock.get("Free Cash Flow", 0) and stock["Free Cash Flow"] > 0:
            score += 10
        if stock.get("Sector") in ["Technology", "Healthcare", "Communication Services"]:
            score += 10
        pe = stock.get("P/E Ratio")
        if pe is not None and pe < 20:
            score += 10
        # הדפסה מפורטת נשארת אופציונלית בשכבת ה-CLI/UI
        return score
