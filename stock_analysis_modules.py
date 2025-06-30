import requests
import yfinance as yf
from bs4 import BeautifulSoup

# ==================== ניתוח צ׳ק ליסט לפי תחומים ====================

def analyze_basic_info(info):
    return {
        "Company Name": info.get("shortName", "N/A"),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Country": info.get("country", "N/A"),
        "Employees": info.get("fullTimeEmployees", "N/A"),
        "Website": info.get("website", "N/A"),
        "Business Summary": info.get("longBusinessSummary", "N/A")[:500]  # חיתוך ל־500 תווים
    }

def analyze_market(info):
    return {
        "Category": info.get("category", "N/A"),
        "Exchange": info.get("exchange", "N/A"),
        "First Mover Advantage": "Unknown (manual input required)",
        "Main Competitors": "Unknown (suggest API or manual input)"
    }

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
        "Return on Equity": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else "N/A"
    }


def analyze_sentiment_external(news_sentiment_score):
    data = {
        "Sentiment Score": news_sentiment_score,
        "Public Opinion": "Derived from sentiment analysis",
    }
    return data

# ✅ שלב 1 – מחזיקי מניות מה-Nasdaq
def get_top_holders(symbol):
    try:
        url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/institutional-holdings"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table")
        rows = table.find_all("tr")[1:6]  # First 5 rows
        print(rows)
        holders = []
        for row in rows:
            cols = row.find_all("td")
            if cols:
                holder_name = cols[0].text.strip()
                holders.append(holder_name)
        return holders
    except Exception as e:
        print(f"❌ Nasdaq scraping failed for {symbol}: {e}")
        return ["N/A"]

# ✅ שלב 2 – שליפת חדשות אסטרטגיות מהמנתח
def get_recent_strategic_news(symbol, news_analyzer):
    try:
        articles = news_analyzer.fetch_news(symbol)
        strategic_news = [a for a in articles if "acquisition" in a["summary"].lower() or "merger" in a["summary"].lower()]
        return [a["summary"] for a in strategic_news[:3]] if strategic_news else ["No strategic news"]
    except:
        return ["Error retrieving news"]

# ✅ ניתוח בעלי מניות
def analyze_shareholders(symbol):
    holders = get_top_holders(symbol)
    return {
        "Top Holders": ", ".join(holders),
        "Institutional Holdings": f"{len(holders)} institutions" if holders[0] != "N/A" else "N/A",
        "Recent Insider Changes": "N/A (manual or SEC API)"
    }

# ✅ ניתוח מהלכים אסטרטגיים
def analyze_strategic_moves(symbol, news_analyzer):
    news = get_recent_strategic_news(symbol, news_analyzer)
    return {
        "Acquisitions / Mergers": "; ".join(news),
        "Recent Strategic Moves": "; ".join(news)
    }
def run_full_analysis(info, news_sentiment_score,symbol=None, news_analyzer=None):
    full_data = {
        **analyze_basic_info(info),
        **analyze_market(info),
        **analyze_management(info),
        **analyze_clients_suppliers(),
        **analyze_financials(info),
        **(analyze_strategic_moves(symbol, news_analyzer) if symbol and news_analyzer else {}),
        **(analyze_shareholders(symbol) if symbol else {}),
        **analyze_sentiment_external(news_sentiment_score),
    }
    print("✅ ניתוח צ'קליסט הושלם")
    return full_data
