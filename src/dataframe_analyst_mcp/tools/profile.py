from __future__ import annotations
from typing import Iterable, Dict, Any
import pandas as pd
import numpy as np

def profile(df: pd.DataFrame, columns: Iterable[str] | None = None, percentiles: Iterable[float] | None = None) -> Dict[str, Any]:
    if columns is None or len(columns) == 0:
        # default numeric columns
        columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    percentiles = list(percentiles or [0.25, 0.5, 0.75])

    stats = {}
    for c in columns:
        s = pd.to_numeric(df[c], errors="coerce")
        if s.dropna().empty:
            stats[str(c)] = {}
            continue
        desc = s.describe(percentiles=percentiles)
        # unify key names
        out = {
        "count": int(desc.get("count", 0)),
        "mean": _num(desc.get("mean")),
        "std": _num(desc.get("std")),
        "min": _num(desc.get("min")),
        "max": _num(desc.get("max")),
    }
        for p in percentiles:
            label = f"{int(p*100)}%"  # pandas usa '25%'/'50%'/'75%'
            key = f"p{int(p*100)}"
            out[key] = _num(desc.get(label))
        stats[str(c)] = out
    return {"stats": stats}

def _num(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except Exception:
        return None
