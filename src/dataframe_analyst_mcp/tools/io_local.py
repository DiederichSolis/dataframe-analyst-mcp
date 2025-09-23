from __future__ import annotations
import os
import pandas as pd

def load_local(path: str, sheet: str | None = None, sep: str | None = None,
               header: int | None = 0, encoding: str | None = None) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Local file not found: {path}")

    lower = path.lower()
    if lower.endswith(".csv") or lower.endswith(".tsv"):
        if sep is None:
            sep = "," if lower.endswith(".csv") else "\t"
        return pd.read_csv(path, sep=sep, header=header, encoding=encoding)
    elif lower.endswith(".xlsx") or lower.endswith(".xls"):
        return pd.read_excel(path, sheet_name=sheet if sheet else 0, header=header, engine="openpyxl" if lower.endswith(".xlsx") else None)
    else:
        raise ValueError(f"Unsupported local file extension: {path}")
