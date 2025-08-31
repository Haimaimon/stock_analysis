# src/stock_analysis/ml/periodic_models.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, List
import joblib
import pandas as pd

_PERIODS: List[str] = ["1d", "1mo", "1y"]

def _artifact_paths(period: str, artifacts_dir: str | Path = "artifacts", legacy_dir: str | Path = "ML"):
    """מאפשר תאימות: קודם מחפש ב-artifacts/, ואם לא קיים – ב-ML/ הישן."""
    artifacts_dir = Path(artifacts_dir)
    legacy_dir = Path(legacy_dir)
    model_a = artifacts_dir / f"model_{period}.pkl"
    feats_a = artifacts_dir / f"features_{period}.pkl"
    model_l = legacy_dir / f"model_{period}.pkl"
    feats_l = legacy_dir / f"features_{period}.pkl"
    model_path = model_a if model_a.exists() else model_l
    feats_path = feats_a if feats_a.exists() else feats_l
    return model_path, feats_path

def _one_hot_sector(raw: dict, feature_names: List[str]) -> dict:
    # אפס לכל תכונת מגזר (Sector_*)
    for col in feature_names:
        if col.startswith("Sector_"):
            raw[col] = 0
    sector_col = f"Sector_{raw.get('Sector', 'Other')}"
    if sector_col in feature_names:
        raw[sector_col] = 1
    return raw

def _raw_row_from_stock(stock: dict) -> dict:
    return {
        "RSI": stock.get("RSI", 50),
        # יתכן שמודל שמור תחת "MACD" ולא "MACD Value" – נבדוק את שניהם
        "MACD": stock.get("MACD", stock.get("MACD Value", 0)),
        "MA20_gt_MA200": int(stock.get("MA20 > MA200", False)),
        "MA50_gt_MA200": int(stock.get("MA50 > MA200", False)),
        "PE_Ratio": stock.get("P/E Ratio", 0),
        "EPS": stock.get("EPS", 0),
        "ProfitMargin": stock.get("Profit Margin (%)", 0),
        "RevenueGrowth": stock.get("Revenue Growth (%)", 0),
        "FreeCashFlow": stock.get("Free Cash Flow", 0),
        "VolumeRatio": stock.get("Volume Ratio", 1),
        "Sector": stock.get("Sector", "Other"),
        "Price (USD)": stock.get("Price (USD)", 0),      # שמיש למודלים עתידיים
        "Sentiment Score": stock.get("Sentiment Score", 0),
    }

def predict_success(stock: dict,
                    periods: List[str] | None = None,
                    artifacts_dir: str | Path = "artifacts",
                    legacy_dir: str | Path = "ML") -> Dict[str, float | None]:
    """
    תואם ל-ML/model_predictor.py המקורי: מחזיר dict עם {"1d": %, "1mo": %, "1y": %}.
    טוען את המודל ואת רשימת הפיצ'רים לכל אופק ומריץ predict_proba.
    """
    periods = periods or _PERIODS
    results: Dict[str, float | None] = {}
    base_row = _raw_row_from_stock(stock)

    for period in periods:
        model_path, feats_path = _artifact_paths(period, artifacts_dir, legacy_dir)
        if (not model_path.exists()) or (not feats_path.exists()):
            results[period] = None
            continue

        try:
            model = joblib.load(model_path)
            feature_names: List[str] = joblib.load(feats_path)

            raw = dict(base_row)  # copy
            raw = _one_hot_sector(raw, feature_names)

            X = pd.DataFrame([raw]).reindex(columns=feature_names, fill_value=0)
            prob = float(model.predict_proba(X)[0][1])
            results[period] = round(prob * 100.0, 2)
        except Exception as e:
            print(f"❌ Prediction error for {period}: {e}")
            results[period] = 0.0

    return results

def predict_success_single(stock: dict,
                           preferred: str = "1mo",
                           artifacts_dir: str | Path = "artifacts",
                           legacy_dir: str | Path = "ML") -> float:
    """
    מחזיר מספר יחיד (ל־UI/סקרינר): קודם ניסיון לפי preferred, ואם אין – ממוצע על הקיימים.
    """
    res = predict_success(stock, artifacts_dir=artifacts_dir, legacy_dir=legacy_dir)
    if res.get(preferred) is not None:
        return float(res[preferred] or 0.0)
    vals = [v for v in res.values() if v is not None]
    return float(sum(vals) / len(vals)) if vals else 0.0
