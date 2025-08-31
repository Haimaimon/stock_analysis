from __future__ import annotations
from ...domain.entities import Signal
from ...domain.ports import AlertSink


import logging
class ConsoleSink(AlertSink):
    async def emit(self, signal: Signal) -> None:
        logging.info("🔔 %s | %s | %s", signal.ticker, signal.ts.strftime('%Y-%m-%d %H:%M:%S %Z'), signal.reason)