# ML/feature_explainer.py

def explain_features(stock):
    explanations = []

    def check(condition, value, description):
        impact = "✅ חיובי" if condition else "❌ שלילי"
        return {"Feature": description, "Value": value, "Impact": impact}

    explanations.append(check(30 <= stock.get("RSI", 100) <= 50, stock.get("RSI"), "RSI באזור oversold מתון"))
    explanations.append(check(stock.get("MACD Value", 0) > 0, stock.get("MACD Value"), "MACD חיובי"))
    explanations.append(check(stock.get("MA50 > MA200", False), stock.get("MA50 > MA200"), "MA50 מעל MA200"))
    explanations.append(check(stock.get("P/E Ratio", 999) < 20, stock.get("P/E Ratio"), "מכפיל רווח נמוך"))
    explanations.append(check(stock.get("EPS", 0) > 0, stock.get("EPS"), "רווח למניה חיובי"))
    explanations.append(check(stock.get("Profit Margin (%)", 0) > 5, stock.get("Profit Margin (%)"), "שולי רווח טובים"))
    explanations.append(check(stock.get("Revenue Growth (%)", 0) > 10, stock.get("Revenue Growth (%)"), "צמיחה בהכנסות"))
    explanations.append(check(stock.get("Free Cash Flow", 0) > 0, stock.get("Free Cash Flow"), "תזרים מזומנים חופשי חיובי"))
    explanations.append(check(stock.get("Sentiment Score", 0) > 0, stock.get("Sentiment Score"), "סנטימנט חיובי"))
    explanations.append(check(stock.get("Sector") in ["Technology", "Healthcare", "Communication Services"],
                              stock.get("Sector"), "סקטור מועדף"))

    return explanations
