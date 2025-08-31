# src/stock_analysis/infrastructure/business/tipranks_client.py
from __future__ import annotations
import requests
from stock_analysis.domain.interfaces import CompetitorClient

class TipRanksClient(CompetitorClient):
    URL = "https://www.tipranks.com/api/symbol/get-similar-symbols?symbol={symbol}"

    def similar_symbols(self, symbol: str) -> list[str]:
        try:
            r = requests.get(self.URL.format(symbol=symbol), timeout=8)
            if r.status_code == 200:
                data = r.json() or {}
                sims = data.get("similar", []) or []
                return [item.get("ticker") for item in sims if item.get("ticker")][:5]
        except Exception:
            pass
        return []
