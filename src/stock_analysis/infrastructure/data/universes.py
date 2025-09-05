# src/stock_analysis/infrastructure/data/universes.py
from pathlib import Path
from typing import List, Optional
import pandas as pd

def _read_symbols_csv(path: Path) -> List[str]:
    if not path.exists():
        return []
    df = pd.read_csv(path)
    col = "Symbol" if "Symbol" in df.columns else df.columns[0]
    return (
        df[col].dropna().astype(str).str.upper().str.strip().unique().tolist()
    )

def load_watchlist(path: Path = Path("data/watchlist.csv")) -> List[str]:
    return _read_symbols_csv(path)

def load_nasdaq_symbols(
    path: Path = Path("data/nasdaq_symbols.csv"),
    max_n: Optional[int] = None,
) -> List[str]:
    syms = _read_symbols_csv(path)
    return syms[:max_n] if max_n else syms
