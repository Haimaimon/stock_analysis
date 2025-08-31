from __future__ import annotations
from dataclasses import dataclass
import math
from typing import List, Dict, Any, Optional

@dataclass
class Decision:
    symbol: str
    score: int                 # 0-100
    go: bool                   # עבר שערי חובה?
    reasons: List[str]         # למה כן/לא
    entry_hint: str            # הצעת טריגר
    stop: Optional[float]
    target: Optional[float]
    shares: int

def _nz(x, d=0.0):
    try: return float(x)
    except Exception: return d

def _clip01(v: float) -> float:
    return max(0.0, min(1.0, v))

def normalize_quality(gap_pct: float|None, rvol: float|None, rs30: float|None,
                      vwap_ok: bool, orh: bool) -> int:
    # RVOL -> 0..100 (ריסון לוגי כדי שלא יתפוצץ)
    rv = max(0.0, _nz(rvol) - 1.0)
    rv_score = 100.0 * (1.0 - math.exp(-rv))           # 1.0 -> ~63, 2.0 -> ~86, 4.0 -> ~98

    gap_score = 100.0 * _clip01((_nz(gap_pct) - 0.2) / (2.0 - 0.2))  # 0.2%..2% → 0..100
    rs_score  = 100.0 * _clip01((_nz(rs30) + 0.5) / (2.0 + 0.5))     # -0.5..+2.0 → 0..100

    base = 0.45*rv_score + 0.35*gap_score + 0.20*rs_score
    bonus = (10.0 if vwap_ok else 0.0) + (10.0 if orh else 0.0)
    return int(round(max(0.0, min(100.0, base + bonus))))

def evaluate_openingbell_row(row: Dict[str, Any], plan: Dict[str, Any]) -> Decision:
    sym   = str(row.get("Symbol"))
    openp = row.get("Open")
    prev  = row.get("Prev Close")
    gap   = row.get("Gap%")
    rvol  = row.get("RVOL")
    vwap  = bool(row.get("VWAP_OK"))
    orh   = bool(row.get("SMA20 > SMA200")) or True  # את אישור ORH בפועל תקבל מה-strategy; כאן לא נחסום
    rs30  = row.get("RS30m") if "RS30m" in row else None  # אם שמרת RS30m ב-attrs, אפשר להוסיף לטבלה

    # שערי חובה (כייל מה-UI)
    MIN_RVOL = 1.2
    MIN_GAP  = 0.3

    go = True
    reasons: List[str] = []
    if rvol is None or rvol < MIN_RVOL:
        go = False; reasons.append(f"❌ RVOL<{MIN_RVOL}")
    else:
        reasons.append("✅ RVOL OK")
    if gap is None or gap < MIN_GAP:
        go = False; reasons.append(f"❌ Gap%<{MIN_GAP}")
    else:
        reasons.append("✅ Gap OK")

    # אופציונלי: דרישת VWAP/ORH
    if vwap: reasons.append("✅ VWAP_OK")
    else:    reasons.append("ℹ️ VWAP not required today")

    score = normalize_quality(gap, rvol, rs30, vwap_ok=vwap, orh=orh)

    # הצעת טריגר
    entry_hint = "Retest ORH then confirmation"
    if not vwap:
        entry_hint = "VWAP reclaim (close back above VWAP with volume)"

    return Decision(
        symbol=sym, score=score, go=go,
        reasons=reasons, entry_hint=entry_hint,
        stop=plan.get("stop"), target=plan.get("target"), shares=int(plan.get("shares") or 0),
    )
