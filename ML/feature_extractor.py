# ML/feature_extractor.py

import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from stock_utils import compute_rsi, compute_macd, analyze_volume

def extract_features(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        if hist.empty or len(hist) < 200:
            return None

        price = info.get("currentPrice", None)
        if not price:
            return None

        ma50 = hist["Close"].rolling(window=50).mean().iloc[-1]
        ma200 = hist["Close"].rolling(window=200).mean().iloc[-1]
        rsi = compute_rsi(hist["Close"])
        macd = compute_macd(hist["Close"])
        volume_ratio, _ = analyze_volume(hist)

        return {
            "Ticker": ticker,
            "RSI": rsi,
            "MACD": macd,
            "MA50_gt_MA200": int(ma50 > ma200),
            "PE_Ratio": info.get("trailingPE", 0),
            "EPS": info.get("trailingEps", 0),
            "ProfitMargin": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else 0,
            "RevenueGrowth": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else 0,
            "FreeCashFlow": info.get("freeCashflow", 0),
            "VolumeRatio": volume_ratio,
            "Sector": info.get("sector", "Other"),
            "Success": 1 if price > hist["Close"].iloc[0] * 1.15 else 0  # הצלחה = עלייה של 15%
        }
    except Exception as e:
        print(f"❌ Error in {ticker}: {e}")
        return None

def batch_extract(symbols, max_threads=10):
    print(f"🚀 Extracting features for {len(symbols)} symbols...")
    results = []

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_symbol = {executor.submit(extract_features, sym): sym for sym in symbols}
        for future in as_completed(future_to_symbol):
            result = future.result()
            if result:
                results.append(result)

    df = pd.DataFrame(results)
    df.dropna(inplace=True)
    print(f"✅ Extracted features for {len(df)} stocks")
    return df
