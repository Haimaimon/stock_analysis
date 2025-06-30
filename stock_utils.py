import pandas as pd
import yfinance as yf
import os
from datetime import datetime
import plotly.graph_objs as go

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def compute_macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    return (ema12 - ema26).iloc[-1]

def analyze_volume(hist):
    avg_volume = hist["Volume"].mean()
    latest_volume = hist["Volume"].iloc[-1]
    volume_ratio = round(latest_volume / avg_volume, 2) if avg_volume else 0
    status = "High" if volume_ratio > 1.5 else "Normal"
    return volume_ratio, status

def generate_forecast(score, sentiment_score):
    combined_score = score + (sentiment_score * 10)
    if combined_score >= 65:
        return "🚀 Strong potential for growth based on technical + sentiment signals."
    elif combined_score >= 50:
        return "📈 Moderate growth potential with mixed indicators."
    else:
        return "🔎 Caution: Limited upside potential."

def plot_candlestick(hist, symbol):
    fig = go.Figure(data=[
        go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Candles'
        )
    ])
    fig.update_layout(title=f'📈 גרף נרות: {symbol}', xaxis_rangeslider_visible=False, height=500)
    return fig

def refresh_sp500_prices(csv_path="sp500_prices.csv"):
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)
    symbols = table[0]['Symbol'].tolist()

    prices = []
    for symbol in symbols:
        try:
            price = yf.Ticker(symbol).info.get("currentPrice", None)
            if price:
                prices.append({"Symbol": symbol, "Price": round(price, 2)})
        except:
            continue

    df = pd.DataFrame(prices)
    df.to_csv(csv_path, index=False)

def get_last_update_date(csv_path="sp500_prices.csv"):
    if os.path.exists(csv_path):
        mod_time = os.path.getmtime(csv_path)
        return datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
    return "לא עודכן עדיין"

def fetch_symbols_with_price_range(min_price, max_price, csv_path="sp500_prices.csv"):
    if not os.path.exists(csv_path):
        refresh_sp500_prices(csv_path)
    df = pd.read_csv(csv_path)
    return df[(df["Price"] >= min_price) & (df["Price"] <= max_price)]["Symbol"].tolist()
