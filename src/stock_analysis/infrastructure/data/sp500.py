# src/stock_analysis/infrastructure/data/sp500.py
from __future__ import annotations
import os
from io import StringIO
from datetime import datetime
from typing import List

import pandas as pd
import requests
import yfinance as yf


WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SYMBOLS_CACHE = "sp500_symbols.csv"        # Cache לרשימת הסימבולים
PRICES_CSV_DEFAULT = "sp500_prices.csv"    # יעד ברירת מחדל לשמירת המחירים


def _fetch_sp500_symbols_from_wikipedia() -> List[str]:
    """מנסה להביא את רשימת הסימבולים מוויקיפדיה עם User-Agent תקין."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(WIKI_URL, headers=headers, timeout=20)
    resp.raise_for_status()

    # קוראים את ה-HTML מקומית כדי לא להיתקע על 403 בתוך read_html
    tables = pd.read_html(StringIO(resp.text))
    # הטבלה הראשונה ברוב המקרים היא רשימת החברות
    df = tables[0]
    # עמודת Symbol קיימת שם; ממירים לפורמט של יאהו (BRK.B -> BRK-B)
    symbols = (
        df["Symbol"]
        .astype(str)
        .str.replace(".", "-", regex=False)
        .tolist()
    )
    return symbols


def _load_symbols_cache() -> List[str] | None:
    if os.path.exists(SYMBOLS_CACHE):
        try:
            cached = pd.read_csv(SYMBOLS_CACHE)
            return cached["Symbol"].astype(str).tolist()
        except Exception:
            return None
    return None


def _save_symbols_cache(symbols: List[str]) -> None:
    pd.DataFrame({"Symbol": symbols}).to_csv(SYMBOLS_CACHE, index=False)


def _get_sp500_symbols() -> List[str]:
    """
    מקור ראשי: ויקיפדיה עם headers. אם נכשל -> טוען מה-Cache המקומי.
    אם אין Cache – זורק שגיאה מפורטת.
    """
    try:
        symbols = _fetch_sp500_symbols_from_wikipedia()
        if symbols:
            _save_symbols_cache(symbols)
            return symbols
    except Exception:
        pass  # ננסה Cache

    cached = _load_symbols_cache()
    if cached:
        return cached
    raise RuntimeError(
        "נכשל בהבאת רשימת ה-S&P 500 מוויקיפדיה ואין Cache מקומי (sp500_symbols.csv). "
        "פתח פעם אחת עם אינטרנט תקין כדי לבנות Cache, או ספק רשימה ידנית."
    )


def _download_last_close_prices(symbols: List[str]) -> pd.DataFrame:
    """
    מוריד ב-BATCH את מחיר ה-Close האחרון עבור כל הסימבולים בעזרת yfinance.download.
    זה חוסך מאות בקשות נפרדות ל-.info ומאיץ משמעותית.
    """
    # yfinance יכול לקבל רשימה גדולה; כדי להיות בטוחים נגד מגבלות URL/Rate – נחלק למנות
    CHUNK_SIZE = 120
    rows = []

    for i in range(0, len(symbols), CHUNK_SIZE):
        chunk = symbols[i:i + CHUNK_SIZE]
        try:
            # period='2d' כדי לוודא שגם אם היום טרם היה Close נקבל את של אתמול
            data = yf.download(
                tickers=chunk,
                period="2d",
                interval="1d",
                auto_adjust=False,
                group_by="ticker",
                threads=True,
                progress=False,
            )
            # שני מצבים: אם יש מספר טיקרים -> MultiIndex/columns; אם טיקר יחיד -> סדרת עמודות אחת
            if isinstance(data.columns, pd.MultiIndex):
                # לוקחים את היום האחרון הזמין לכל טיקר
                last_idx = data.index.max()
                close_slice = data.xs("Close", axis=1, level=1)
                if last_idx in close_slice.index:
                    last_row = close_slice.loc[last_idx].dropna()
                    rows.extend(
                        [{"Symbol": sym, "Price": round(float(price), 2)}
                         for sym, price in last_row.items()]
                    )
            else:
                # טיקר יחיד: data עמודה בשם "Close"
                last_idx = data.index.max()
                if "Close" in data.columns and last_idx is not None:
                    price = data.loc[last_idx, "Close"]
                    if pd.notna(price):
                        rows.append({"Symbol": chunk[0], "Price": round(float(price), 2)})
        except Exception:
            # נמשיך למנה הבאה; אפשר להוסיף כאן לוג/איסוף שגיאות אם תרצה
            continue

    return pd.DataFrame(rows)


def refresh_sp500_prices(csv_path: str = PRICES_CSV_DEFAULT) -> None:
    """
    מרענן את מחירי ה-S&P 500 לקובץ CSV בצורה מהירה ועמידה:
    1) מביא רשימת סימבולים (ויקיפדיה עם User-Agent + Cache).
    2) מוריד מחירי Close אחרונים ב-BATCH דרך yfinance.download.
    3) כותב CSV.
    """
    symbols = _get_sp500_symbols()
    prices_df = _download_last_close_prices(symbols)

    # אופציונלי: לוודא שכל הסימבולים קיימים – ממזגים כדי לראות מי חסר
    out = pd.DataFrame({"Symbol": symbols}).merge(
        prices_df, on="Symbol", how="left"
    )

    out.to_csv(csv_path, index=False)


def get_last_update_date(csv_path: str = PRICES_CSV_DEFAULT) -> str:
    if os.path.exists(csv_path):
        mod_time = os.path.getmtime(csv_path)
        return datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
    return "לא עודכן עדיין"
