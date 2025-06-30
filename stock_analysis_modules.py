import yfinance as yf

# ==================== ניתוח צ׳ק ליסט לפי תחומים ====================

def analyze_basic_info(info):
    data = {
        "Company Name": info.get("shortName"),
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
        "Business Summary": info.get("longBusinessSummary"),
        "Country": info.get("country"),
        "Employees": info.get("fullTimeEmployees"),
    }
    return data

def analyze_market(info):
    data = {
        "Category": info.get("category"),
        "Is First Mover": "N/A (manual input)",
        "Competitors": "N/A (manual or API-dependent)",
    }
    return data

def analyze_management(info):
    ceo = info.get("companyOfficers", [{}])[0].get("name", "Unknown")
    data = {
        "CEO": ceo,
        "Founder In Charge": "N/A (manual input)",
        "Background": "N/A (LinkedIn/News)",
    }
    return data

def analyze_clients_suppliers():
    data = {
        "Key Customers": "N/A (manual input)",
        "Supplier Risk": "N/A (manual input)",
    }
    return data

def analyze_financials(info):
    data = {
        "Market Cap": info.get("marketCap"),
        "P/E Ratio": info.get("trailingPE"),
        "EPS": info.get("trailingEps"),
        "Profit Margin": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else None,
        "Revenue Growth (%)": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else None,
        "Free Cash Flow": info.get("freeCashflow"),
        "Debt to Equity": info.get("debtToEquity"),
        "Beta": info.get("beta"),
    }
    return data

def analyze_strategic_moves():
    data = {
        "Acquisitions": "N/A (manual or from news API)",
        "Recent Strategic Moves": "N/A (manual)",
    }
    return data

def analyze_shareholders():
    data = {
        "Top Holders": "N/A (can pull from Finviz or Nasdaq API)",
        "Institutional Holdings": "N/A",
        "Recent Insider Changes": "N/A",
    }
    return data

def analyze_sentiment_external(news_sentiment_score):
    data = {
        "Sentiment Score": news_sentiment_score,
        "Public Opinion": "Derived from sentiment analysis",
    }
    return data

def run_full_analysis(info, news_sentiment_score):
    full_data = {
        **analyze_basic_info(info),
        **analyze_market(info),
        **analyze_management(info),
        **analyze_clients_suppliers(),
        **analyze_financials(info),
        **analyze_strategic_moves(),
        **analyze_shareholders(),
        **analyze_sentiment_external(news_sentiment_score),
    }
    print("✅ ניתוח צ'קליסט הושלם")
    return full_data
