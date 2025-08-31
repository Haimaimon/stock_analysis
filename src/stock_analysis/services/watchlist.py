from __future__ import annotations
from pathlib import Path
import json
from typing import List

class WatchlistService:
    def __init__(self, path: str = ".watchlist.json"):
        self.path = Path(path)

    def load(self) -> List[str]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def save(self, symbols: List[str]) -> None:
        self.path.write_text(json.dumps(sorted(list(set([s.upper() for s in symbols]))), ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, symbol: str) -> List[str]:
        xs = self.load()
        xs.append(symbol.upper())
        self.save(xs)
        return xs

    def remove(self, symbol: str) -> List[str]:
        xs = [s for s in self.load() if s.upper() != symbol.upper()]
        self.save(xs)
        return xs
