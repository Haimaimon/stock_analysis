from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import pandas as pd

from stock_analysis.strategies import registry as strategy_registry
from stock_analysis.strategies.filters import OpeningBellFilterConfig, openingbell_quality_checks
from stock_analysis.services.risk import build_trade_plan

@dataclass
class BacktestConfig:
    only_buy: bool = True
    atr_mult_stop: float = 1.2
    rr_ratio: float = 2.0
    risk_budget_usd: float = 100.0

class OpeningBellBacktester:
    def __init__(self, data_provider, intraday_period="30d", intraday_interval="5m"):
        self.dp = data_provider
        self.period = intraday_period
        self.interval = intraday_interval
        self.cfg_filter = OpeningBellFilterConfig()
        self.cfg_bt = BacktestConfig()

    def run(self, symbols: List[str]) -> Tuple[pd.DataFrame, float]:
        strat = strategy_registry.get("OpeningBell")
        rows = []
        for sym in symbols:
            try:
                df = strat.run(sym, self.dp, period=self.period, interval=self.interval)
                if df is None or df.empty or ("is_opening" not in df.columns) or (not df["is_opening"].any()):
                    continue
                open_idx = df.index[df["is_opening"]][0]
                pos = list(df.index).index(open_idx)
                prev_close = float(df.iloc[pos-1]["Close"]) if pos > 0 else None
                qc = openingbell_quality_checks(df, open_idx, prev_close, self.cfg_filter)
                entry = float(df.loc[open_idx, "Open"])
                plan = build_trade_plan(sym, entry, qc["atr"], self.cfg_filter.atr_mult_stop, self.cfg_bt.rr_ratio, self.cfg_bt.risk_budget_usd)
                # יציאה פשוטה: Close של סוף היום
                same_day = df.index.date == pd.to_datetime(open_idx).date()
                day_df = df.loc[same_day]
                exit_price = float(day_df["Close"].iloc[-1]) if not day_df.empty else entry
                pnl = (exit_price - entry) * (plan.shares if plan else 0)
                rows.append({
                    "Symbol": sym, "Entry": entry, "Exit": exit_price, "Shares": plan.shares if plan else 0,
                    "PnL($)": round(pnl, 2), "Gap%": qc["gap_pct"], "RVOL": qc["rvol"], "VWAP_OK": qc["vwap_ok"]
                })
            except Exception:
                continue
        df_out = pd.DataFrame(rows).sort_values(by="PnL($)", ascending=False)
        total = float(df_out["PnL($)"].sum()) if not df_out.empty else 0.0
        return df_out, total
