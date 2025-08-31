# src/stock_analysis/infrastructure/business/wiki_client.py
from __future__ import annotations
from typing import Mapping, Any
import requests
from stock_analysis.domain.interfaces import WikipediaClient

class WikipediaHttpClient(WikipediaClient):
    BASE = "https://en.wikipedia.org/api/rest_v1/page/summary/"

    def page_summary(self, title: str) -> Mapping[str, Any] | None:
        try:
            r = requests.get(self.BASE + title, timeout=8)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None
