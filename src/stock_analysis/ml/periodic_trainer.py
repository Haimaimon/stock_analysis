# src/stock_analysis/ml/periodic_trainer.py
from __future__ import annotations
from pathlib import Path
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# תאימות לשכבת הדאטה שלך:
from stock_utils import refresh_sp500_prices  # compat

# batch_extract: נחפש קודם בחבילה החדשה (תקבל בהודעה הבאה), ואם אין – ב-ML הישן
try:
    from stock_analysis.ml.feature_extractor import batch_extract  # type: ignore
except Exception:
    from ML.feature_extractor import batch_extract  # type: ignore

def train_models(artifacts_dir: str | Path = "artifacts",
                 save_legacy_copy: bool = True) -> None:
    """מכשיר מודלים לכל אופק ושומר:
       artifacts/model_{period}.pkl + artifacts/features_{period}.pkl
       ואם save_legacy_copy=True אז גם ב-ML/ לשמירת תאימות."""
    artifacts_dir = Path(artifacts_dir)
    legacy_dir = Path("ML")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    legacy_dir.mkdir(parents=True, exist_ok=True)

    refresh_sp500_prices()
    symbols_df = pd.read_csv("sp500_prices.csv")
    symbols = symbols_df["Symbol"].tolist()

    df = batch_extract(symbols)  # מצופה לכלול: Ticker, Sector, Success_1d/1mo/1y + פיצ'רים
    df = pd.get_dummies(df, columns=["Sector"])

    X_all = df.drop(columns=["Ticker", "Success_1d", "Success_1mo", "Success_1y"])
    y_map = {"1d": df["Success_1d"], "1mo": df["Success_1mo"], "1y": df["Success_1y"]}

    for period, y in y_map.items():
        model = RandomForestClassifier(n_estimators=150, random_state=42, max_depth=6)
        model.fit(X_all, y.astype(int))

        print(f"📊 [{period}] Classification Report:")
        print(classification_report(y, model.predict(X_all)))

        # save artifacts/
        model_p = artifacts_dir / f"model_{period}.pkl"
        feats_p = artifacts_dir / f"features_{period}.pkl"
        joblib.dump(model, model_p)
        joblib.dump(list(X_all.columns), feats_p)
        print(f"✅ Saved {model_p.name}, {feats_p.name} in {artifacts_dir}")

        # optional legacy copies in ML/
        if save_legacy_copy:
            joblib.dump(model, legacy_dir / f"model_{period}.pkl")
            joblib.dump(list(X_all.columns), legacy_dir / f"features_{period}.pkl")
            print(f"↩️  Also saved legacy copies in {legacy_dir}")
