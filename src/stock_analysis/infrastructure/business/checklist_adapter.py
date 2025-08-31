# src/stock_analysis/infrastructure/business/checklist_adapter.py
from __future__ import annotations
from typing import Mapping, Any

from stock_analysis.domain.interfaces import BusinessChecklist, SentimentAnalyzer
from stock_analysis.services.business.checklist_service import ChecklistService
from stock_analysis.infrastructure.business.wiki_client import WikipediaHttpClient
from stock_analysis.infrastructure.business.tipranks_client import TipRanksClient
from stock_analysis.infrastructure.business.holders_yf import YFinanceHoldersProvider

class BusinessChecklistAdapter(BusinessChecklist):
    """Adapts the new ChecklistService to the BusinessChecklist protocol."""
    def __init__(self):
        self.service = ChecklistService(
            wiki=WikipediaHttpClient(),
            competitors=TipRanksClient(),
            holders=YFinanceHoldersProvider(),
        )

    def __call__(self, info: Mapping[str, Any], sentiment_score: float, symbol: str, analyzer: SentimentAnalyzer) -> dict:
        return self.service.run(info, sentiment_score, symbol, analyzer)


# ---- תאימות לאחור: מספק פונקציה זהה לשם ולחתימה המקוריים ----
def run_full_analysis(info: Mapping[str, Any], news_sentiment_score: float, symbol: str | None = None, news_analyzer: SentimentAnalyzer | None = None) -> dict:
    """
    drop-in replacement לפונקציה המקורית שלך.
    משתמש ב-ChecklistService מאחורי הקלעים, כך שכל קוד ישן שמייבא run_full_analysis ימשיך לעבוד.
    """
    adapter = BusinessChecklistAdapter()
    if symbol and news_analyzer:
        return adapter(info, news_sentiment_score, symbol, news_analyzer)
    # אם אין סימבול/אנלייזר – נחזיר את המינימום האפשרי מהשירות
    return adapter.service.run(info, news_sentiment_score, symbol, news_analyzer)
