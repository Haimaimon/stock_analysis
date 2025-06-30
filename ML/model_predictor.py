# ML/model_predictor.py

import joblib
import pandas as pd
import os

# טוען את המודל ואת שמות הפיצ'רים
model_path = "ML/trained_model.pkl"
feature_path = "ML/feature_names.pkl"

model = joblib.load(model_path) if os.path.exists(model_path) else None
feature_names = joblib.load(feature_path) if os.path.exists(feature_path) else []

def predict_success(stock):
    if not model or not feature_names:
        print("❌ Model or feature names not found.")
        return 0

    try:
        raw_data = {
            "RSI": stock.get("RSI", 50),
            "MACD": stock.get("MACD", 0),
            "MA50_gt_MA200": int(stock.get("MA50 > MA200", False)),
            "PE_Ratio": stock.get("P/E Ratio", 0),
            "EPS": stock.get("EPS", 0),
            "ProfitMargin": stock.get("Profit Margin (%)", 0),
            "RevenueGrowth": stock.get("Revenue Growth (%)", 0),
            "FreeCashFlow": stock.get("Free Cash Flow", 0),
            "VolumeRatio": stock.get("Volume Ratio", 1),
        }

        # הוספת כל הסקטורים האפשריים עם ערך 0
        for col in feature_names:
            if col.startswith("Sector_"):
                raw_data[col] = 0

        # הפעלה של הסקטור המתאים ל־1 אם הוא קיים
        sector = stock.get("Sector", "Other")
        sector_col = f"Sector_{sector}"
        if sector_col in feature_names:
            raw_data[sector_col] = 1

        # יצירת DataFrame עם כל העמודות הנדרשות
        full_data = pd.DataFrame([raw_data])
        full_data = full_data.reindex(columns=feature_names, fill_value=0)

        # חיזוי הסתברות
        prob = model.predict_proba(full_data)[0][1]
        return round(prob * 100, 2)

    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return 0
