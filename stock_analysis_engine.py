import yfinance as yf
from stock_utils import (
    compute_rsi, compute_macd, analyze_volume,
    generate_forecast
)
from stock_analysis_modules import run_full_analysis

# ב־:
from ML.model_predictor import predict_success

def score_stock(stock):
    score = 0
    if 30 <= stock.get("RSI", 100) <= 50: score += 10
    if stock.get("MACD Positive"): score += 10
    if stock.get("MA50 > MA200"): score += 10
    if stock.get("Revenue Growth (%)", 0) > 10: score += 15
    if stock.get("Profit Margin (%)", 0) > 5: score += 10
    if stock.get("Free Cash Flow", 0) and stock["Free Cash Flow"] > 0: score += 10
    if stock.get("Sector") in ["Technology", "Healthcare", "Communication Services"]: score += 10
    if stock.get("P/E Ratio") and stock["P/E Ratio"] < 20: score += 10
    return score

def fetch_stock_data(symbol, analyzer, min_price, max_price):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        hist = ticker.history(period="1y")
        if hist.empty or len(hist) < 200:
            print(f"⚠️ אין מספיק היסטוריית מחיר למניה {symbol}")
            return None
        print(f"✅ YFinance: נטען היסטוריית מחירים ({len(hist)} ימים)")

        price = info.get("currentPrice", None)
        if not price:
            print(f"❌ אין מחיר נוכחי עבור {symbol}")
            return None
        if price < min_price or price > max_price:
            print(f"⛔ מחיר {price} לא בטווח: {min_price}–{max_price}")
            return None

        # Indicators
        ma50 = hist["Close"].rolling(window=50).mean().iloc[-1]
        ma200 = hist["Close"].rolling(window=200).mean().iloc[-1]

        rsi = compute_rsi(hist["Close"])
        macd_value = compute_macd(hist["Close"])
        macd_pos = compute_macd(hist["Close"]) > 0
        volume_ratio, volume_status = analyze_volume(hist)

        # Sentiment
        sentiment_data, _ = analyzer.run_full_analysis(symbol)

        # ניתוח עסקי
        checklist = run_full_analysis(info, sentiment_data["Sentiment Score"], symbol, analyzer)

        # ✅ הרכבת תוצאה (כולל פיצ'רים חדשים + שמות תואמים למודל)
        stock = {
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
            "MA50 > MA200": ma50 > ma200 if ma50 and ma200 else False,
            "RSI": round(rsi, 2),
            "MACD Positive": macd_pos,
            "MACD Value": macd_value,  # <== חובה בשביל המודל
            "Volume Ratio": volume_ratio,
            "Volume Status": volume_status,
            "Sentiment Score": sentiment_data["Sentiment Score"],
            "Ticker": ticker,
            "History": hist,
            "Business Checklist": checklist,
        }

        stock["Smart Score"] = score_stock(stock)
        stock["Forecast"] = generate_forecast(stock["Smart Score"], stock["Sentiment Score"])
        stock["AI Success Probability (%)"] = predict_success(stock)
        return stock

    except Exception as e:
        print(f"❌ שגיאה בניתוח מניה {symbol}: {e}")
        return None

