from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from ...domain.trading import Position, PositionStatus

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
POS_FILE = DATA_DIR / "positions.json"

def save_positions(positions: dict[str, Position]) -> None:
    out = {}
    for t, p in positions.items():
        out[t] = {
            "ticker": p.ticker,
            "status": p.status.value,
            "qty": p.qty,
            "entry_price": p.entry_price,
            "tp_price": p.tp_price,
            "sl_price": p.sl_price,
            "opened_at": p.opened_at.isoformat(),
            "closed_at": p.closed_at.isoformat() if p.closed_at else None,
            "exit_price": p.exit_price,
            "pnl_pct": p.pnl_pct,
        }
    POS_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
