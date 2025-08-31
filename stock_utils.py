# stock_utils.py  (compat layer – לשים במקום הקובץ הישן)
from __future__ import annotations
import pandas as pd

# --- Feature equivalents ---
from stock_analysis.features.rsi import compute_rsi_last as compute_rsi
from stock_analysis.features.macd import compute_macd_last as compute_macd
from stock_analysis.features.volume import analyze_volume_snapshot as analyze_volume

# --- Utils / Presentation ---
from stock_analysis.utils.forecast import generate_forecast
from stock_analysis.presentation.plotting import plot_candlestick

# --- Data infra / Symbols ---
from stock_analysis.infrastructure.data.sp500 import refresh_sp500_prices, get_last_update_date
from stock_analysis.infrastructure.data.nasdaq import refresh_nasdaq_prices
from stock_analysis.utils.symbols import (
    fetch_symbols_with_price_range,
    load_sp500_symbols,
    load_nasdaq_symbols,
)
