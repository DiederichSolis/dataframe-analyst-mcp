from __future__ import annotations
import pandas as pd

def missing_report(df: pd.DataFrame) -> list[dict]:
    total = len(df)
    if total == 0:
        return [{"column": str(c), "pct": 0.0} for c in df.columns]
    res = []
    for c in df.columns:
        pct = float(df[c].isna().sum()) * 100.0 / float(total)
        res.append({"column": str(c), "pct": round(pct, 4)})
    return res
