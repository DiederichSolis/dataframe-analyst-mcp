from __future__ import annotations
import pandas as pd

def infer_schema(df: pd.DataFrame) -> list[dict]:
    schema = []
    for col in df.columns:
        s = df[col]
        # Basic dtype mapping
        dtype = str(s.dtype)
        nullable = s.isna().any()
        schema.append({"name": str(col), "dtype": dtype, "nullable": bool(nullable)})
    return schema
