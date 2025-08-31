from __future__ import annotations

def explain_features(stock: dict):
    explanations = []
    total_score = 0

    def check(condition, value, description, points):
        nonlocal total_score
        impact = "✅ חיובי" if condition else "❌ שלילי"
        if condition:
            total_score += points
        return {
            "Feature": description,
            "Value": value if value is not None else "N/A",
            "Impact": impact,
            "Points": points if condition else 0,
        }

    def safe_get(key, default=0):
        try:
            value = stock.get(key)
            return default if value is None or value == "N/A" else value
        except Exception:
            return default

    explanations.append(check(30 <= safe_get("RSI", 100) <= 50, stock.get("RSI"), "RSI באזור oversold מתון", 10))
    explanations.append(check(safe_get("MACD Value", stock.get("MACD", 0)) > 0,
                              stock.get("MACD Value", stock.get("MACD")), "MACD חיובי", 10))
    explanations.append(check(stock.get("MA20 > MA200", False), stock.get("MA20 > MA200"), "MA20 מעל MA200", 10))
    explanations.append(check(stock.get("MA50 > MA200", False), stock.get("MA50 > MA200"), "MA50 מעל MA200", 10))

    pe_ratio = safe_get("P/E Ratio", None)
    explanations.append(check(pe_ratio is not None and pe_ratio < 20, pe_ratio, "מכפיל רווח נמוך", 10))

    explanations.append(check(safe_get("EPS", 0) > 0, stock.get("EPS"), "רווח למניה חיובי", 0))  # לא תורם לניקוד כרגע
    explanations.append(check(safe_get("Profit Margin (%)", 0) > 5, stock.get("Profit Margin (%)"), "שולי רווח טובים", 10))
    explanations.append(check(safe_get("Revenue Growth (%)", 0) > 10, stock.get("Revenue Growth (%)"), "צמיחה בהכנסות", 15))
    explanations.append(check(safe_get("Free Cash Flow", 0) > 0, stock.get("Free Cash Flow"), "תזרים מזומנים חופשי חיובי", 10))
    explanations.append(check(safe_get("Sentiment Score", 0) > 0, stock.get("Sentiment Score"), "סנטימנט חיובי", 0))  # לא תורם לניקוד
    explanations.append(check(stock.get("Sector") in ["Technology", "Healthcare", "Communication Services"],
                              stock.get("Sector"), "סקטור מועדף", 10))

    explanations.append({
        "Feature": "**סך הניקוד (Smart Score)**",
        "Value": f"{total_score}/100",
        "Impact": "💡 סיכום",
        "Points": total_score,
    })

    return explanations
