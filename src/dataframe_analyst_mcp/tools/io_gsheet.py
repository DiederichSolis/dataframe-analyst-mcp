from __future__ import annotations
from typing import Optional, List
import pandas as pd

def _authorize_gspread():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(
        filename=get_sa_path(), scopes=scopes
    )
    gc = gspread.authorize(creds)
    return gc

def get_sa_path() -> str:
    import os
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS env var not set.")
    if not os.path.exists(path):
        raise RuntimeError(f"Service account file not found: {path}")
    return path

def read_gsheet(spreadsheet_id: str, worksheet: Optional[str] = None, cell_range: Optional[str] = None, header: int | None = 0) -> pd.DataFrame:
    gc = _authorize_gspread()
    sh = gc.open_by_key(spreadsheet_id)
    ws = None
    if worksheet:
        ws = sh.worksheet(worksheet)
    else:
        ws = sh.sheet1
    values: List[List[str]] = ws.get(cell_range) if cell_range else ws.get_all_values()
    if not values:
        return pd.DataFrame()
    df = pd.DataFrame(values)
    if header is None:
        # no header row
        return df
    else:
        # header row index
        df.columns = df.iloc[header]
        df = df.drop(df.index[: header + 1]).reset_index(drop=True)
        return df
