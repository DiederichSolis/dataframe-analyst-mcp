from __future__ import annotations
from typing import Dict, Any
import pandas as pd

def groupby(df: pd.DataFrame, by: list[str], metrics: Dict[str, list[str]]) -> Dict[str, Any]:
    # Ensure numeric for metric columns
    df2 = df.copy()
    for col in metrics.keys():
        df2[col] = pd.to_numeric(df2[col], errors="coerce")

    agg_dict = {}
    for col, funcs in metrics.items():
        agg_dict[col] = funcs

    g = df2.groupby(by).agg(agg_dict).reset_index()

    # flatten MultiIndex columns
    g.columns = ["_".join(filter(None, map(str, c))).strip("_") if isinstance(c, tuple) else str(c) for c in g.columns]
    # e.g., categoria, precio_mean, precio_max, cantidad_sum
    records = g.to_dict(orient="records")
    return {"groups": records}
