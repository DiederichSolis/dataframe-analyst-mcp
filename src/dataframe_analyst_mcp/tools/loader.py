from __future__ import annotations
from typing import Any, Dict, Optional
import pandas as pd
from .io_local import load_local
from .io_gsheet import read_gsheet
from .io_gdrive import download_file_to_tmp

def load_data(source: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> tuple[pd.DataFrame, dict]:
    options = options or {}
    stype = source.get("type")
    header = options.get("header", 0)

    if stype == "local":
        path = source["path"]
        df = load_local(
            path=path,
            sheet=options.get("sheet"),
            sep=options.get("sep"),
            header=header,
            encoding=options.get("encoding"),
        )
        meta = {"type": "local", "path": path}
        return df, meta

    elif stype == "gsheet":
        spreadsheet_id = source["spreadsheetId"]
        worksheet = source.get("worksheet")
        rng = source.get("range")
        df = read_gsheet(spreadsheet_id=spreadsheet_id, worksheet=worksheet, cell_range=rng, header=header)
        meta = {"type": "gsheet", "spreadsheetId": spreadsheet_id, "worksheet": worksheet or "sheet1", "range": rng}
        return df, meta

    elif stype == "gdrive_file":
        file_id = source["fileId"]
        tmp = download_file_to_tmp(file_id)
        df = load_local(
            path=tmp,
            sheet=options.get("sheet"),
            sep=options.get("sep"),
            header=header,
            encoding=options.get("encoding"),
        )
        meta = {"type": "gdrive_file", "fileId": file_id, "tmp_path": tmp}
        return df, meta

    else:
        raise ValueError(f"Unknown source.type: {stype}")
