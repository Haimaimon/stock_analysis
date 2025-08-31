from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable, Mapping
from stock_analysis.domain.entities import StrategySignal
import pandas as pd

class SignalRepository:
    def __init__(self, db_path: str = "signals.db") -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, strategy TEXT, open_time TEXT,
                open_price REAL, prev_close REAL,
                gap_pct REAL, rvol REAL, vwap_ok INTEGER,
                sma20 REAL, sma200 REAL, reason TEXT, decision TEXT
            )
            """)
            con.commit()

    def save(self, s: StrategySignal) -> None:
        with self._conn() as con:
            con.execute("""
                INSERT INTO signals(symbol,strategy,open_time,open_price,prev_close,gap_pct,rvol,vwap_ok,sma20,sma200,reason,decision)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (s.symbol, s.strategy, s.open_time, s.open_price, s.prev_close, s.gap_pct, s.rvol,
                  1 if s.vwap_ok else 0 if s.vwap_ok is not None else None,
                  s.sma20, s.sma200, s.reason, s.decision))
            con.commit()

    def fetch_latest(self, limit: int = 200):
        with self._conn() as con:
            cur = con.execute("SELECT symbol,strategy,open_time,decision,gap_pct,rvol,vwap_ok FROM signals ORDER BY id DESC LIMIT ?", (limit,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        
    def to_dataframe(self, since_days: int = 7) -> pd.DataFrame:
        if not Path(self.db_path).exists():
            return pd.DataFrame()
        con = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM signals", con)
        finally:
            con.close()
        if "open_time" in df.columns:
            df["open_time"] = pd.to_datetime(df["open_time"], errors="coerce")
            if since_days:
                cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=since_days)
                df = df[df["open_time"] >= cutoff]
        return df