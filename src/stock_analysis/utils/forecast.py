# src/stock_analysis/utils/forecast.py
def generate_forecast(score: int | float, sentiment_score: float) -> str:
    combined = float(score) + (float(sentiment_score) * 10.0)
    if combined >= 65:
        return "🚀 Strong potential for growth based on technical + sentiment signals."
    elif combined >= 50:
        return "📈 Moderate growth potential with mixed indicators."
    else:
        return "🔎 Caution: Limited upside potential."
