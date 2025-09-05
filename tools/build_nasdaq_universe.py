# tools/build_nasdaq_universe.py
import io, time, random, pathlib
import pandas as pd
import requests

OUT = pathlib.Path("data/nasdaq_symbols.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

PRIMARY = "https://api.nasdaqtrader.com/dynamic/symdir/nasdaqtraded.txt"
ALT_HTTP = "http://api.nasdaqtrader.com/dynamic/symdir/nasdaqtraded.txt"
ALT_HOST = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqtraded.txt"

def _download_txt(url: str, retries: int = 4, timeout: int = 20) -> str | None:
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            wait = min(2 * (i + 1), 10) + random.uniform(0, 0.5)
            print(f"[WARN] fetch failed from {url}: {e} | retrying in {wait:.1f}s")
            time.sleep(wait)
    return None

def _parse_symbols(txt: str) -> list[str]:
    df = pd.read_csv(io.StringIO(txt), sep="|")
    df = df[(df["Nasdaq Traded"] == "Y") & (df["ETF"] == "N")]
    syms = (
        df["Symbol"]
        .dropna()
        .astype(str).str.upper().str.strip()
        .unique().tolist()
    )
    # הסרה של סימבולים לא “רגילים” (OTC, עם נקודות/קווים חריגים) – עדין
    return [s for s in syms if s.isalnum()]

def main():
    txt = _download_txt(PRIMARY)
    if txt is None:
        txt = _download_txt(ALT_HTTP)
    if txt is None:
        txt = _download_txt(ALT_HOST)

    symbols: list[str] = []
    if txt:
        try:
            symbols = _parse_symbols(txt)
        except Exception as e:
            print(f"[WARN] parse failed, will try yfinance fallback: {e}")

    # Fallback: yfinance אם קיים
    if not symbols:
        try:
            import yfinance as yf
            symbols = yf.tickers_nasdaq()
            # yfinance מחזיר גם ETF/OTC לפעמים – סינון עדין
            symbols = [s.strip().upper() for s in symbols if s and s.strip().isalpha()]
            print(f"[INFO] Loaded {len(symbols)} symbols via yfinance.tickers_nasdaq()")
        except Exception as e:
            print(f"[ERROR] Could not load NASDAQ symbols via any source: {e}")

    if not symbols:
        raise SystemExit("No NASDAQ symbols could be loaded. Check internet/DNS or run again later.")

    pd.DataFrame({"Symbol": symbols}).to_csv(OUT, index=False)
    print(f"[OK] Saved {len(symbols)} symbols -> {OUT}")

if __name__ == "__main__":
    main()
