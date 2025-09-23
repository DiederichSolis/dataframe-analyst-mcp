from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel

from .state import STATE
from .tools.loader import load_data
from .tools.schema import infer_schema
from .tools.missing import missing_report
from .tools.profile import profile as profile_tool
from .tools.corr import correlation
from .tools.outliers import detect_outliers
from .tools.groupby import groupby as groupby_tool
from .tools.export_report import export_report as export_report_tool

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------
# Modelos Pydantic para entradas (FastMCP generará el input_schema)
# ---------------------------------------------------------------------

# load_data
class SourceLocal(BaseModel):
    type: Literal["local"]
    path: str

class SourceGDriveFile(BaseModel):
    type: Literal["gdrive_file"]
    fileId: str

class SourceGSheet(BaseModel):
    type: Literal["gsheet"]
    spreadsheetId: str
    range: Optional[str] = None
    sheet: Optional[Union[int, str]] = None

LoadSource = Union[SourceLocal, SourceGDriveFile, SourceGSheet]

class LoadOptions(BaseModel):
    sep: Optional[str] = None
    header: Optional[int] = None
    encoding: Optional[str] = None

# export_report
class DestLocal(BaseModel):
    type: Literal["local"]
    path: str

class DestGDriveFolder(BaseModel):
    type: Literal["gdrive_folder"]
    folderId: str

Dest = Union[DestLocal, DestGDriveFolder]

# ---------------------------------------------------------------------
# FastMCP app
# ---------------------------------------------------------------------
app = FastMCP("dataframe-analyst-mcp")

@app.tool("load_data")
async def _load_data(source: LoadSource, options: Optional[LoadOptions] = None) -> Dict[str, Any]:
    """
    Load data into the session. Supports:
      - local: path
      - gdrive_file: fileId
      - gsheet: spreadsheetId (+range/sheet opcionales)
    """
    df, meta = load_data(source.model_dump(), options.model_dump() if options else None)
    STATE.set_df(df, meta)
    preview = df.head(5).to_dict(orient="records")
    return {
        "ok": True,
        "columns": list(map(str, df.columns)),
        "rows": int(getattr(df, "shape", (0, 0))[0]),
        "rows_preview": preview,
        "source_meta": meta,
    }

@app.tool("infer_schema")
async def _infer_schema() -> Dict[str, Any]:
    """Infer column dtypes and basic info for the current dataset."""
    df = STATE.require_df()
    return {"ok": True, "schema": infer_schema(df)}

@app.tool("missing_report")
async def _missing_report() -> Dict[str, Any]:
    """Missing values summary per column (count/ratio)."""
    df = STATE.require_df()
    return {"ok": True, "missing_pct": missing_report(df)}

@app.tool("profile")
async def _profile(
    columns: Optional[List[str]] = None,
    percentiles: Optional[List[float]] = None
) -> Dict[str, Any]:
    """Descriptive stats for numeric columns; optional column subset."""
    df = STATE.require_df()
    return {"ok": True, **profile_tool(df, columns=columns, percentiles=percentiles)}

@app.tool("correlation")
async def _correlation(method: Literal["pearson", "spearman", "kendall"] = "pearson") -> Dict[str, Any]:
    """Correlation matrix with the chosen method."""
    df = STATE.require_df()
    return {"ok": True, "method": method, "matrix": correlation(df, method=method)}

@app.tool("detect_outliers")
async def _detect_outliers(
    column: str,
    method: Literal["iqr", "zscore"] = "iqr",
    factor: float = 1.5,
    z: float = 3.0
) -> Dict[str, Any]:
    """Detect outliers on a numeric column (IQR/Z-score)."""
    df = STATE.require_df()
    return {"ok": True, **detect_outliers(df, column=column, method=method, factor=factor, z=z)}

@app.tool("groupby")
async def _groupby(by: List[str], metrics: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Group by keys and apply aggregations.
    metrics ejemplo: {"price": ["mean","sum"], "qty": ["sum"]}
    """
    df = STATE.require_df()
    return {"ok": True, "result": groupby_tool(df, by=by, metrics=metrics)}

@app.tool("export_report")
async def _export_report(dest: Dest, fmt: Literal["md", "json", "html"], sections: List[str]) -> Dict[str, Any]:
    """Export report to local file or Drive folder."""
    # dest y fmt ya están validados por Pydantic
    d = dest.model_dump()
    return {"ok": True, **export_report_tool(d, fmt=fmt, sections=sections)}

# ---------------------------------------------------------------------
# CLI fallback (opcional)
# ---------------------------------------------------------------------
def cli_loop():
    print("DataFrame Analyst CLI (fallback). Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("df> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line in ("exit", "quit"):
            break
        if line == "help":
            print(
                "commands:\n"
                "  load_data {json}\n"
                "  infer_schema\n"
                "  missing_report\n"
                "  profile {json}\n"
                "  correlation {json}\n"
                "  detect_outliers {json}\n"
                "  groupby {json}\n"
                "  export_report {json}   # clave 'fmt'\n"
            )
            continue

        cmd, *rest = line.split(" ", 1)
        arg = {}
        if rest:
            try:
                arg = json.loads(rest[0])
            except Exception as e:
                print(f"Invalid JSON: {e}")
                continue

        try:
            if cmd == "load_data":
                df, meta = load_data(arg.get("source"), arg.get("options"))
                STATE.set_df(df, meta)
                prev = df.head(5).to_dict(orient="records")
                print(json.dumps(
                    {"ok": True, "columns": list(map(str, df.columns)), "rows_preview": prev, "source_meta": meta},
                    indent=2, ensure_ascii=False
                ))
            elif cmd == "infer_schema":
                df = STATE.require_df()
                print(json.dumps({"ok": True, "schema": infer_schema(df)}, indent=2, ensure_ascii=False))
            elif cmd == "missing_report":
                df = STATE.require_df()
                print(json.dumps({"ok": True, "missing_pct": missing_report(df)}, indent=2, ensure_ascii=False))
            elif cmd == "profile":
                df = STATE.require_df()
                print(json.dumps(
                    {"ok": True, **profile_tool(df, columns=arg.get("columns"), percentiles=arg.get("percentiles"))},
                    indent=2, ensure_ascii=False
                ))
            elif cmd == "correlation":
                df = STATE.require_df()
                method = arg.get("method", "pearson")
                print(json.dumps({"ok": True, "method": method, "matrix": correlation(df, method=method)},
                                 indent=2, ensure_ascii=False))
            elif cmd == "detect_outliers":
                df = STATE.require_df()
                print(json.dumps(
                    {"ok": True, **detect_outliers(
                        df,
                        column=arg["column"],
                        method=arg.get("method", "iqr"),
                        factor=arg.get("factor", 1.5),
                        z=arg.get("z", 3.0)
                    )},
                    indent=2, ensure_ascii=False
                ))
            elif cmd == "groupby":
                df = STATE.require_df()
                print(json.dumps({"ok": True, "result": groupby_tool(df, by=arg["by"], metrics=arg["metrics"])},
                                 indent=2, ensure_ascii=False))
            elif cmd == "export_report":
                print(json.dumps(
                    {"ok": True, **export_report_tool(arg["dest"], fmt=arg["fmt"], sections=arg["sections"])},
                    indent=2, ensure_ascii=False
                ))
            else:
                print("Unknown command. Type 'help'.")
        except Exception as e:
            print(f"Error: {e}")

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcp", action="store_true", help="Run MCP stdio server")
    parser.add_argument("--cli", action="store_true", help="Run CLI fallback")
    args = parser.parse_args()

    if args.mcp:
        # STDIO por defecto
        app.run()  # <-- reemplaza app.run_stdio() por esto
        # (si quieres ser explícito): app.run(transport="stdio")
    elif args.cli:
        cli_loop()
    else:
        print("Use --mcp to run MCP server or --cli for local CLI.")

if __name__ == "__main__":
    main()
