from __future__ import annotations
import os
from dataclasses import dataclass

from stock_analysis.infrastructure.data_providers.yfinance_provider import YFinanceProvider
from stock_analysis.infrastructure.models.success_predictor_adapter import SuccessPredictorAdapter
from stock_analysis.infrastructure.business.checklist_adapter import BusinessChecklistAdapter
from stock_analysis.services.screener import Screener, ScreenerConfig
from stock_analysis.features.pipeline import Pipeline
from stock_analysis.features.rsi import RSI
from stock_analysis.features.macd import MACD
from stock_analysis.features.sma import SMA
from stock_analysis.features.volume import VolumeStatus

from finnhub_news import FinnhubNewsAnalyzer

@dataclass
class AppConfig:
    min_price: float = 8.0
    max_price: float = 14.0

def build_screener(min_price: float, max_price: float) -> Screener:
    dp = YFinanceProvider()
    analyzer = FinnhubNewsAnalyzer(api_key=os.getenv("FINNHUB_API_KEY", ""))
    checklist = BusinessChecklistAdapter()
    success = SuccessPredictorAdapter(horizon="1mo")

    pipeline = Pipeline([
        RSI(period=14, out_col="RSI"),
        MACD(span_fast=12, span_slow=26, out_col="MACD Value"),
        SMA(window=20), SMA(window=50), SMA(window=200),
        VolumeStatus(out_ratio_col="Volume Ratio", out_status_col="Volume Status"),
    ])

    cfg = ScreenerConfig(
        min_price=min_price, max_price=max_price,
        history_period="1y", history_interval="1d",
        intraday_period="5d", intraday_interval="5m",
    )
    return Screener(dp, analyzer, checklist, success, daily_pipeline=pipeline, cfg=cfg)
