from __future__ import annotations
from typing import Iterable, List
from ...domain.entities import Signal
from ...domain.ports import AlertSink

class MultiSink(AlertSink):
    def __init__(self, sinks: Iterable[AlertSink]) -> None:
        self.sinks: List[AlertSink] = list(sinks)

    async def emit(self, signal: Signal) -> None:
        for s in self.sinks:
            try:
                await s.emit(signal)
            except Exception as e:
                # לא מפיל את כולם אם אחד נכשל
                print(f"[MultiSink] sink error: {e}")
