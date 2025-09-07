from __future__ import annotations
import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from .state import STATE
from .tools.loader import load_data
from .tools.schema import infer_schema
from .tools.missing import missing_report
from .tools.profile import profile as profile_tool
from .tools.corr import correlation
from .tools.outliers import detect_outliers
from .tools.groupby import groupby as groupby_tool
from .tools.export_report import export_report as export_report_tool

# ---------- MCP wiring (via stdio) ----------
# We try to use the "mcp" python SDK if available. If not, fallback CLI is still usable.
def build_mcp_app():
    from mcp.server import Server
    server = Server("csv-processor-mcp")

    @server.tool("load_data", description="Load data from local/gdrive_file/gsheet into session")
    async def _load_data(source: Dict[str, Any], options: Optional[Dict[str, Any]] = None):
        df, meta = load_data(source, options)
        STATE.set_df(df, meta)
        prev = df.head(5).to_dict(orient="records")
        return {"columns": list(map(str, df.columns)), "rows_preview": prev, "source_meta": meta}

    @server.tool("infer_schema", description="Infer simple schema for current dataset")
    async def _infer_schema():
        df = STATE.require_df()
        return {"schema": infer_schema(df)}

    @server.tool("missing_report", description="Missing values by column (%)")
    async def _missing_report():
        df = STATE.require_df()
        return {"missing_pct": missing_report(df)}

    @server.tool("profile", description="Basic stats and percentiles for numeric columns")
    async def _profile(columns: Optional[List[str]] = None, percentiles: Optional[List[float]] = None):
        df = STATE.require_df()
        return profile_tool(df, columns=columns, percentiles=percentiles)

    @server.tool("correlation", description="Correlation matrix for numeric columns")
    async def _correlation(method: str = "pearson"):
        df = STATE.require_df()
        return correlation(df, method=method)

    @server.tool("detect_outliers", description="Detect outliers in a numeric column (IQR/Z-score)")
    async def _detect_outliers(column: str, method: str = "iqr", factor: float = 1.5, z: float = 3.0):
        df = STATE.require_df()
        return detect_outliers(df, column=column, method=method, factor=factor, z=z)

    @server.tool("groupby", description="Groupby aggregations")
    async def _groupby(by: List[str], metrics: Dict[str, List[str]]):
        df = STATE.require_df()
        return groupby_tool(df, by=by, metrics=metrics)

    @server.tool("export_report", description="Export report to local or Google Drive")
    async def _export_report(dest: Dict[str, Any], format: str, sections: List[str]):
        return export_report_tool(dest, fmt=format, sections=sections)

    return server

async def run_mcp_stdio():
    try:
        from mcp.server.stdio import stdio_server
    except Exception as e:
        raise RuntimeError("MCP SDK not available. Use --cli fallback.") from e

    server = build_mcp_app()
    srv = stdio_server(server)
    await srv.serve()

# ---------- CLI fallback ----------
def cli_loop():
    print("CSV Processor CLI (fallback). Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("csv> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line in ("exit", "quit"):
            break
        if line == "help":
            print("commands: load_data <json>, infer_schema, missing_report, profile <json>, correlation <json>, detect_outliers <json>, groupby <json>, export_report <json>")
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
                print(json.dumps({"columns": list(map(str, df.columns)), "rows_preview": prev, "source_meta": meta}, indent=2, ensure_ascii=False))

            elif cmd == "infer_schema":
                df = STATE.require_df()
                print(json.dumps({"schema": infer_schema(df)}, indent=2, ensure_ascii=False))

            elif cmd == "missing_report":
                df = STATE.require_df()
                print(json.dumps({"missing_pct": missing_report(df)}, indent=2, ensure_ascii=False))

            elif cmd == "profile":
                df = STATE.require_df()
                print(json.dumps(profile_tool(df, columns=arg.get("columns"), percentiles=arg.get("percentiles")), indent=2, ensure_ascii=False))

            elif cmd == "correlation":
                df = STATE.require_df()
                method = arg.get("method", "pearson")
                print(json.dumps(correlation(df, method=method), indent=2, ensure_ascii=False))

            elif cmd == "detect_outliers":
                df = STATE.require_df()
                print(json.dumps(detect_outliers(df, column=arg["column"], method=arg.get("method","iqr"), factor=arg.get("factor",1.5), z=arg.get("z",3.0)), indent=2, ensure_ascii=False))

            elif cmd == "groupby":
                df = STATE.require_df()
                print(json.dumps(groupby_tool(df, by=arg["by"], metrics=arg["metrics"]), indent=2, ensure_ascii=False))

            elif cmd == "export_report":
                print(json.dumps(export_report_tool(arg["dest"], fmt=arg["format"], sections=arg["sections"]), indent=2, ensure_ascii=False))

            else:
                print("Unknown command. Type 'help'.")
        except Exception as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcp", action="store_true", help="Run MCP stdio server")
    parser.add_argument("--cli", action="store_true", help="Run CLI fallback")
    args = parser.parse_args()

    if args.mcp:
        asyncio.run(run_mcp_stdio())
    elif args.cli:
        cli_loop()
    else:
        print("Use --mcp to run MCP server or --cli for local CLI.")

if __name__ == "__main__":
    main()
