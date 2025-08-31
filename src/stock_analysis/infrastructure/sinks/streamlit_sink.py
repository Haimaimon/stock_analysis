from __future__ import annotations
import json, os, time
from pathlib import Path
from ...domain.entities import Signal
from ...domain.ports import AlertSink

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
SIGNALS_FILE = DATA_DIR / "signals.jsonl"

class StreamlitSink(AlertSink):
    async def emit(self, signal: Signal) -> None:
        # כותב שורת JSON אחת (append) – Streamlit יקרא וירענן
        line = {
            "ticker": signal.ticker,
            "ts": signal.ts.isoformat(),
            "reason": signal.reason
        }
        with open(SIGNALS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
