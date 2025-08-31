from __future__ import annotations
from typing import Dict, List
from .base import Strategy

# ייבוא האסטרטגיות
from .opening_bell import OpeningBellStrategy
from stock_analysis.strategies.openingbell_plus import OpeningBellPlus

_strategies: Dict[str, Strategy] = {}

def register(name: str, strategy: Strategy) -> None:
    # רישום בשם נתון וגם Case-insensitive
    _strategies[name] = strategy
    _strategies[name.lower()] = strategy

def get(name: str) -> Strategy:
    try:
        return _strategies[name]
    except KeyError:
        try:
            return _strategies[name.lower()]
        except KeyError:
            raise KeyError(name)

def available() -> List[str]:
    # מציגים רק את המפתחות "היפים" (Case-sensitive המקוריים)
    nice = [k for k in _strategies.keys() if k.lower() != k]
    return sorted(nice) if nice else sorted(set(_strategies.keys()))

# ---- רישום ברירת מחדל ----
register("OpeningBell", OpeningBellStrategy())

# ---- רישום האסטרטגיה המשודרגת ----
register("OpeningBell+", OpeningBellPlus())
