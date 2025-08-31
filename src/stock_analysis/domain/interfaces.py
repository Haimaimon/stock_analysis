# src/stock_analysis/domain/interfaces.py
from typing import Protocol, runtime_checkable, Mapping, Any, Sequence
import pandas as pd

@runtime_checkable
class DataProvider(Protocol):
    def info(self, symbol: str) -> Mapping[str, Any]: ...
    def history(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame: ...
    def last_price(self, symbol: str) -> float | None: ...

@runtime_checkable
class SentimentAnalyzer(Protocol):
    def run_full_analysis(self, symbol: str) -> tuple[dict, Any]: ...
    def fetch_news(self, symbol: str) -> Sequence[Mapping[str, Any]]: ...

@runtime_checkable
class BusinessChecklist(Protocol):
    def __call__(self, info: Mapping[str, Any], sentiment_score: float, symbol: str, analyzer: SentimentAnalyzer) -> dict: ...

# משלים – כדי שסקרינר יוכל לקבל מודל חיזוי דרך הזרקת תלותים
@runtime_checkable
class SuccessPredictor(Protocol):
    def predict_success(self, stock_features: Mapping[str, Any]) -> float: ...
    # מחזיר אחוזים (0–100) לפי ההגדרה שלנו באדפטר

# הרחבות לעושר מידע (ויקי/מתחרים/מחזיקים)
@runtime_checkable
class WikipediaClient(Protocol):
    def page_summary(self, title: str) -> Mapping[str, Any] | None: ...

@runtime_checkable
class CompetitorClient(Protocol):
    def similar_symbols(self, symbol: str) -> list[str]: ...

@runtime_checkable
class HoldersProvider(Protocol):
    def top_institutional_holders(self, symbol: str, top_n: int = 5) -> list[str]: ...
