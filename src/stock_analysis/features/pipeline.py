# src/stock_analysis/features/pipeline.py
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from typing import Protocol, List

class FeatureStep(Protocol):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...

@dataclass
class Pipeline:
    steps: List[FeatureStep]

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df
        for step in self.steps:
            out = step.transform(out)
        return out
