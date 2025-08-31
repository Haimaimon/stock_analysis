# src/stock_analysis/presentation/api/main.py
from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from stock_analysis.ml.periodic_models import predict_success as predict_success_all
from stock_analysis.ml.feature_explainer import explain_features

from stock_analysis.infrastructure.data_providers.yfinance_provider import YFinanceProvider
from stock_analysis.infrastructure.models.success_predictor_adapter import SuccessPredictorAdapter
from stock_analysis.infrastructure.business.checklist_adapter import BusinessChecklistAdapter
from stock_analysis.services.screener import Screener, ScreenerConfig
from stock_analysis.features.pipeline import Pipeline
from stock_analysis.features.rsi import RSI
from stock_analysis.features.macd import MACD
from stock_analysis.features.sma import SMA
from stock_analysis.features.volume import VolumeStatus
from stock_analysis.strategies import registry as strategy_registry

# Your existing analyzer
from finnhub_news import FinnhubNewsAnalyzer

app = FastAPI(title="StockAnalysis API", version="1.0")

def build_screener(min_price=8.0, max_price=14.0) -> Screener:
    dp = YFinanceProvider()
    analyzer = FinnhubNewsAnalyzer(api_key=os.getenv("FINNHUB_API_KEY", ""))
    checklist = BusinessChecklistAdapter()
    success = SuccessPredictorAdapter()
    pipeline = Pipeline([
        RSI(period=14, out_col="RSI"),
        MACD(span_fast=12, span_slow=26, out_col="MACD Value"),
        SMA(window=20), SMA(window=50), SMA(window=200),
        VolumeStatus(out_ratio_col="Volume Ratio", out_status_col="Volume Status"),
    ])
    cfg = ScreenerConfig(min_price=min_price, max_price=max_price)
    return Screener(dp, analyzer, checklist, success, daily_pipeline=pipeline, cfg=cfg)

class DailyReq(BaseModel):
    symbol: str
    min_price: float = 8.0
    max_price: float = 14.0

class IntradayReq(BaseModel):
    symbol: str
    strategy: str = "OpeningBell"

@app.get("/strategies")
def strategies():
    return {"strategies": strategy_registry.available()}

@app.post("/daily")
def daily(req: DailyReq):
    sc = build_screener(req.min_price, req.max_price)
    res = sc.analyze_daily(req.symbol.upper())
    if res is None:
        raise HTTPException(status_code=404, detail="Symbol not found or conditions not met")
    # Convert DF to json-serializable where needed
    res = {k: (v.to_dict() if hasattr(v, "to_dict") else v) for k, v in res.items() if k != "History"}
    return res

@app.post("/intraday")
def intraday(req: IntradayReq):
    sc = build_screener()
    if req.strategy not in strategy_registry.available():
        raise HTTPException(status_code=400, detail="Unknown strategy")
    df = sc.analyze_intraday_with_strategy(req.symbol.upper(), req.strategy)
    if df is None:
        raise HTTPException(status_code=404, detail="No intraday data")
    # Return tail 100 rows for brevity
    return df.tail(100).reset_index().to_dict(orient="records")

@app.post("/predict/horizons")
def predict_horizons(req: DailyReq):
    sc = build_screener(req.min_price, req.max_price)
    res = sc.analyze_daily(req.symbol.upper())
    if res is None:
        raise HTTPException(status_code=404, detail="Symbol not found or conditions not met")
    return predict_success_all(res)

@app.post("/explain")
def explain(req: DailyReq):
    sc = build_screener(req.min_price, req.max_price)
    res = sc.analyze_daily(req.symbol.upper())
    if res is None:
        raise HTTPException(status_code=404, detail="Symbol not found or conditions not met")
    return explain_features(res)
