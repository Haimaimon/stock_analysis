# src/stock_analysis/infrastructure/models/success_predictor_adapter.py
from stock_analysis.ml.periodic_models import predict_success_single

class SuccessPredictorAdapter:
    def __init__(self, horizon: str = "1mo"):
        self.horizon = horizon
    def predict_success(self, stock_features: dict) -> float:
        return float(predict_success_single(stock_features, preferred=self.horizon))
