from datetime import datetime, timedelta
from transformers import pipeline
import requests

class FinnhubNewsAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

    def fetch_news(self, symbol):
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')

        url = "https://finnhub.io/api/v1/company-news"
        params = {"symbol": symbol, "from": from_date, "to": to_date, "token": self.api_key}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ שגיאה בשליפת חדשות מ־Finnhub עבור {symbol}: {e}")
            return []

    def analyze_sentiment(self, articles):
        sentiments = []
        for article in articles:
            text = article.get("headline", "") + ". " + article.get("summary", "")
            if text.strip():
                result = self.sentiment_model(text[:512])[0]
                sentiments.append(result["label"])

        total = len(sentiments)
        pos = sentiments.count("POSITIVE")
        neg = sentiments.count("NEGATIVE")
        neu = sentiments.count("NEUTRAL") if "NEUTRAL" in sentiments else total - pos - neg

        return {
            "Total Articles": total,
            "Positive": pos,
            "Negative": neg,
            "Neutral": neu,
            "Sentiment Score": round((pos - neg) / total, 2) if total > 0 else 0
        }

    def run_full_analysis(self, symbol):
        news = self.fetch_news(symbol)
        sentiment_result = self.analyze_sentiment(news)
        return sentiment_result, news
