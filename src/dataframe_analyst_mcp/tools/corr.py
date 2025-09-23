from __future__ import annotations
from typing import Dict, Any
import pandas as pd

def correlation(df: pd.DataFrame, method: str = "pearson") -> Dict[str, Any]:
    num_df = df.copy()
    for c in num_df.columns:
        num_df[c] = pd.to_numeric(num_df[c], errors="coerce")
    corr = num_df.corr(method=method)
    corr = corr.fillna(0.0)
    matrix = []
    for col in corr.columns:
        row = {"col": str(col), "to": {str(c): float(corr.loc[col, c]) for c in corr.columns}}
        matrix.append(row)
    return {"matrix": matrix}
