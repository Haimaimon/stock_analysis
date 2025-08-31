# src/stock_analysis/services/business/checklist_service.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any, Sequence

from stock_analysis.domain.interfaces import (
    SentimentAnalyzer, WikipediaClient, CompetitorClient, HoldersProvider
)

@dataclass
class ChecklistService:
    wiki: WikipediaClient
    competitors: CompetitorClient
    holders: HoldersProvider

    # ---------- מודולים זהים שלך, עטופים כפונקציות פרטיות ----------
    def _analyze_basic_info(self, info: Mapping[str, Any]) -> dict:
        return {
            "Company Name": info.get("shortName", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Industry": info.get("industry", "N/A"),
            "Currency": info.get("currency", "N/A"),
            "Country": info.get("country", "N/A"),
            "Employees": info.get("fullTimeEmployees", "N/A"),
            "Website": info.get("website", "N/A"),
            "Business Summary": (info.get("longBusinessSummary", "N/A") or "")[:500],
        }

    def _analyze_market(self, info: Mapping[str, Any]) -> dict:
        sector = info.get("sector")
        industry = info.get("industry")
        category = f"{sector} - {industry}" if sector and industry else "N/A"
        return {
            "Category": category,
            "Exchange": info.get("exchange", "N/A"),
            "First Mover Advantage": "Unknown (manual input required)",
            "Main Competitors": "Unknown (suggest API or manual input)",
        }

    def _analyze_management(self, info: Mapping[str, Any]) -> dict:
        officers = info.get("companyOfficers", []) or []
        ceo = "Unknown"
        if isinstance(officers, list) and officers:
            ceo = officers[0].get("name", "Unknown")
        return {"CEO": ceo}

    def _analyze_clients_suppliers(self) -> dict:
        return {
            "Key Customers": "N/A (manual input)",
            "Supplier Risk": "N/A (manual input)",
        }

    def _analyze_financials(self, info: Mapping[str, Any]) -> dict:
        return {
            "Market Cap": info.get("marketCap", "N/A"),
            "P/E Ratio": info.get("trailingPE", "N/A"),
            "EPS": info.get("trailingEps", "N/A"),
            "Profit Margin (%)": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else "N/A",
            "Revenue Growth (%)": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else "N/A",
            "Free Cash Flow": info.get("freeCashflow", "N/A"),
            "Debt to Equity": info.get("debtToEquity", "N/A"),
            "Beta": info.get("beta", "N/A"),
            "Forward PE": info.get("forwardPE", "N/A"),
            "Return on Equity": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else "N/A",
        }

    def _analyze_sentiment_external(self, news_sentiment_score: float) -> dict:
        return {
            "Sentiment Score": news_sentiment_score,
            "Public Opinion": "Derived from sentiment analysis",
        }

    def _get_recent_strategic_news(self, symbol: str, news_analyzer: SentimentAnalyzer) -> list[str]:
        try:
            articles: Sequence[Mapping[str, Any]] = news_analyzer.fetch_news(symbol)  # בהנחה שקיים אצלך
            def is_strategic(a: Mapping[str, Any]) -> bool:
                s = (a.get("summary") or "").lower()
                return ("acquisition" in s) or ("merger" in s)
            strategic = [a for a in articles if is_strategic(a)]
            if not strategic:
                return ["No strategic news"]
            return [(a.get("summary") or "") for a in strategic[:3]]
        except Exception:
            return ["Error retrieving news"]

    def _analyze_strategic_moves(self, symbol: str, news_analyzer: SentimentAnalyzer) -> dict:
        news = self._get_recent_strategic_news(symbol, news_analyzer)
        joined = "; ".join(news)
        return {
            "Acquisitions / Mergers": joined,
            "Recent Strategic Moves": joined,
        }

    def _analyze_shareholders(self, symbol: str) -> dict:
        top = self.holders.top_institutional_holders(symbol, top_n=5)
        return {
            "Top Holders": ", ".join(top) if top else "N/A",
            "Institutional Holdings": f"{len(top)} institutions" if top and top[0] != "N/A" else "N/A",
            "Recent Insider Changes": "N/A (manual or SEC API)",
        }

    def _wiki_data(self, title: str | None) -> dict:
        if not title:
            return {}
        data = self.wiki.page_summary(title) or {}
        return {
            "Background": (data.get("extract") or "")[:500],
            "Founded": data.get("description", ""),
        }

    def _competitors(self, symbol: str | None) -> str:
        if not symbol:
            return "N/A"
        try:
            sims = self.competitors.similar_symbols(symbol)
            return ", ".join(sims[:5]) if sims else "N/A"
        except Exception:
            return "N/A"

    # ---------- נקודת הכניסה השירותית (המקבילה ל-run_full_analysis) ----------
    def run(self, info: Mapping[str, Any], news_sentiment_score: float, symbol: str | None, news_analyzer: SentimentAnalyzer | None) -> dict:
        out = {
            **self._analyze_basic_info(info),
            **self._analyze_market(info),
            **self._analyze_management(info),
            **self._analyze_clients_suppliers(),
            **self._analyze_financials(info),
            **(self._analyze_strategic_moves(symbol, news_analyzer) if symbol and news_analyzer else {}),
            **(self._analyze_shareholders(symbol) if symbol else {}),
            **self._analyze_sentiment_external(news_sentiment_score),
            "Competitors": self._competitors(symbol),
            **self._wiki_data(symbol),
        }
        print("✅ ניתוח צ'קליסט הושלם")
        return out
