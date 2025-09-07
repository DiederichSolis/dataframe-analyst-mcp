from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np

def detect_outliers(df: pd.DataFrame, column: str, method: str = "iqr", factor: float = 1.5, z: float = 3.0) -> Dict[str, Any]:
    s = pd.to_numeric(df[column], errors="coerce")
    idx = []
    if method == "iqr":
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        mask = (s < lower) | (s > upper)
        idx = list(s[mask].index)
    elif method == "zscore":
        mu = s.mean()
        sd = s.std(ddof=0)
        if sd == 0 or np.isnan(sd):
            idx = []
        else:
            mask = (np.abs((s - mu) / sd) > z)
            idx = list(s[mask].index)
    else:
        raise ValueError("method must be 'iqr' or 'zscore'")
    outliers = [{"row": int(i), "value": _num(s.loc[i])} for i in idx]
    return {"outliers": outliers, "count": len(outliers)}

def _num(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(v)
