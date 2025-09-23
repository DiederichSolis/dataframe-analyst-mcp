from __future__ import annotations
from typing import Dict, Any, List
import os
from ..state import STATE
from .schema import infer_schema
from .missing import missing_report
from .profile import profile
from .corr import correlation
from .outliers import detect_outliers
from .io_gdrive import upload_bytes_to_drive

def export_report(dest: Dict[str, Any], fmt: str, sections: List[str]) -> Dict[str, Any]:
    df = STATE.require_df()
    parts = []
    if fmt not in ("md", "json", "html"):
        raise ValueError("format must be md/json/html")

    # Compose content
    if "schema" in sections:
        parts.append(render_section("Schema", infer_schema(df)))
    if "missing" in sections:
        parts.append(render_section("Missing", missing_report(df)))
    if "profile" in sections:
        parts.append(render_section("Profile", profile(df)))
    if "corr" in sections or "correlation" in sections:
        parts.append(render_section("Correlation", correlation(df)))
    if "outliers" in sections and len(df.columns) > 0:
        # default on first numeric column (heuristic)
        num_cols = [c for c in df.columns if str(df[c].dtype).startswith(("float", "int"))]
        if num_cols:
            parts.append(render_section(f"Outliers ({num_cols[0]})", detect_outliers(df, num_cols[0])))
    content = "\n\n".join(parts) if fmt == "md" else to_json_or_html(parts, fmt)

    dtyp = dest.get("type")
    if dtyp == "local":
        path = dest["path"]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"saved": True, "dest": {"type": "local", "path": path}}

    elif dtyp == "gdrive":
        folder_id = dest["folderId"]
        filename = dest["filename"]
        mime = dest.get("mime", "text/markdown" if fmt == "md" else "application/json")
        overwrite = bool(dest.get("overwrite", True))
        info = upload_bytes_to_drive(folder_id=folder_id, filename=filename, content=content.encode("utf-8"), mime=mime, overwrite=overwrite)
        return {"saved": True, "dest": {"type": "gdrive", **info}}

    else:
        raise ValueError("dest.type must be local or gdrive")

def render_section(title: str, obj: Any) -> str:
    import json
    return f"## {title}\n\n```json\n{json.dumps(obj, indent=2, ensure_ascii=False)}\n```"

def to_json_or_html(parts: list[str], fmt: str) -> str:
    if fmt == "json":
        import json
        # parts are markdown strings; for json, we just wrap them as sections
        return json.dumps({"sections": parts}, indent=2, ensure_ascii=False)
    elif fmt == "html":
        body = "".join(f"<section><pre>{escape_html(p)}</pre></section>" for p in parts)
        return f"<!doctype html><html><head><meta charset='utf-8'><title>Report</title></head><body>{body}</body></html>"
    else:
        raise ValueError(fmt)

def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
