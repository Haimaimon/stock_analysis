# src/stock_analysis/features/volume.py
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import Tuple

@dataclass
class VolumeStatus:
    high_threshold: float = 1.5
    out_ratio_col: str = "Volume Ratio"
    out_status_col: str = "Volume Status"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        avg_vol = out["Volume"].mean()
        latest = out["Volume"].iloc[-1]
        ratio = round(latest / avg_vol, 2) if avg_vol else 0.0
        status = "High" if ratio > self.high_threshold else "Normal"
        out[self.out_ratio_col] = ratio
        out[self.out_status_col] = status
        return out

def analyze_volume_snapshot(hist: pd.DataFrame) -> Tuple[float, str]:
    avg_volume = hist["Volume"].mean()
    latest_volume = hist["Volume"].iloc[-1]
    volume_ratio = round(latest_volume / avg_volume, 2) if avg_volume else 0.0
    status = "High" if volume_ratio > 1.5 else "Normal"
    return volume_ratio, status
