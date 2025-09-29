"""
Finance numeric grounding - blocks hallucinations by verifying claims against data
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Tuple, Optional
from datetime import date
import bisect

class TimeSeries(BaseModel):
    series_id: str
    freq: Literal["D","W","M","Q","A"] = "M"
    points: List[Tuple[date, float]]

class NumericClaim(BaseModel):
    id: str
    metric: str
    operator: Literal["=","<", "<=" ,">", ">=","change","yoy","qoq"]
    value: float
    at: Optional[date] = None
    window: Optional[int] = None  # days when operator=="change"

class Evidence(BaseModel):
    claim_id: str
    supported: bool
    source_series: Optional[str] = None
    details: dict = Field(default_factory=dict)

def _nearest_idx(dates, target):
    """Find nearest index for target date"""
    i = bisect.bisect_left(dates, target)
    return min(max(i, 0), len(dates)-1)

def verify_claim(c: NumericClaim, s: TimeSeries) -> Evidence:
    """Verify a single numeric claim against time series data"""
    dates = [d for d,_ in s.points]
    vals = [v for _,v in s.points]
    
    if not dates: 
        return Evidence(
            claim_id=c.id, 
            supported=False, 
            source_series=s.series_id, 
            details={"reason":"empty_series"}
        )
    
    idx = _nearest_idx(dates, c.at or dates[-1])
    v = vals[idx]
    det = {"at": str(dates[idx]), "value": v}

    if c.operator in {"=","<", "<=" ,">", ">="}:
        ok = ((c.operator=="=" and abs(v-c.value)<1e-9) or
              (c.operator=="<" and v < c.value) or
              (c.operator=="<=" and v <= c.value) or
              (c.operator==">" and v > c.value) or
              (c.operator==">=" and v >= c.value))
        return Evidence(claim_id=c.id, supported=ok, source_series=s.series_id, details=det)

    if c.operator=="change":
        win = c.window or 30
        # naive day-window; for M/Q/A use index-1
        j = max(idx-1,0)
        chg = v - vals[j]
        det.update({"prev_at": str(dates[j]), "prev": vals[j], "change": chg})
        return Evidence(claim_id=c.id, supported=abs(chg-c.value)<1e-9, source_series=s.series_id, details=det)

    if c.operator in {"yoy","qoq"}:
        # Validate frequency for YoY/QoQ operations
        if c.operator == "yoy" and s.freq not in {"M", "Q", "A"}:
            return Evidence(
                claim_id=c.id, 
                supported=False, 
                source_series=s.series_id, 
                details={"reason":"invalid_frequency_for_yoy", "freq":s.freq, "required":["M","Q","A"]}
            )
        if c.operator == "qoq" and s.freq not in {"M", "Q"}:
            return Evidence(
                claim_id=c.id, 
                supported=False, 
                source_series=s.series_id, 
                details={"reason":"invalid_frequency_for_qoq", "freq":s.freq, "required":["M","Q"]}
            )
        
        step = {"M":12,"Q":4,"A":1}.get(s.freq, 12) if c.operator=="yoy" else {"M":3,"Q":1}.get(s.freq, 3)
        j = max(idx-step,0)
        
        # Check if we have enough historical data
        if j >= len(vals):
            return Evidence(
                claim_id=c.id, 
                supported=False, 
                source_series=s.series_id, 
                details={"reason":"insufficient_historical_data", "required_periods":step, "available":idx}
            )
        
        pct = ((v/vals[j])-1.0)*100.0 if vals[j] != 0 else None
        det.update({"prev_at": str(dates[j]), "prev": vals[j], "pct": pct, "snapped_date": str(dates[idx])})
        ok = (pct is not None) and (abs(pct - c.value) <= 0.05)  # 5bp tolerance
        return Evidence(claim_id=c.id, supported=ok, source_series=s.series_id, details=det)

    return Evidence(
        claim_id=c.id, 
        supported=False, 
        source_series=s.series_id, 
        details={"reason":"unsupported_operator"}
    )

def ground_claims(claims: list[NumericClaim], series: list[TimeSeries]) -> tuple[list[Evidence], bool]:
    """Verify all claims against available time series data"""
    by_id = {s.series_id: s for s in series}
    ev: list[Evidence] = []
    all_ok = True
    
    for c in claims:
        s = by_id.get(c.metric)
        if not s:
            ev.append(Evidence(
                claim_id=c.id, 
                supported=False, 
                details={"reason":"series_not_found","metric":c.metric}
            ))
            all_ok = False
            continue
        
        e = verify_claim(c, s)
        ev.append(e)
        all_ok = all_ok and e.supported
    
    return ev, all_ok
