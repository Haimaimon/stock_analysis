# ML/model_trainer.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
from stock_utils import refresh_sp500_prices
from ML.feature_extractor import batch_extract

def train_model():
    refresh_sp500_prices()
    symbols_df = pd.read_csv("sp500_prices.csv")
    symbols = symbols_df["Symbol"].tolist()
    
    df = batch_extract(symbols)
    df = pd.get_dummies(df, columns=["Sector"])  # One-hot encoding

    X = df.drop(columns=["Success", "Ticker"])
    y = df["Success"]

    model = RandomForestClassifier(n_estimators=150, random_state=42, max_depth=6)
    model.fit(X, y)

    print("🎯 Classification Report:")
    print(classification_report(y, model.predict(X)))

    joblib.dump(model, "ML/trained_model.pkl")
    joblib.dump(X.columns.tolist(), "ML/feature_names.pkl")
    print("✅ Model + Features saved")

if __name__ == "__main__":
    train_model()
