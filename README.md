# dataframe-analyst-mcp

Servidor **MCP** (Model Context Protocol) y **CLI** para análisis exploratorio de datos (**CSV/XLS/XLSX/Google Sheets/Google Drive**) y exporte de reportes (**md/json/html**) a **disco local** o **Google Drive**.

Implementado con **FastMCP** (autogenera los `inputSchema` a partir de *type hints* / Pydantic).

---

## Características (no triviales)
- **Carga de datos** desde:
  - **Local** (`path` a CSV/XLS/XLSX).
  - **Google Drive (fileId)**.
  - **Google Sheets (spreadsheetId + range/sheet opcional)**.
- **Herramientas MCP** expuestas:
  - `load_data` – carga dataset y deja una vista previa en sesión.
  - `infer_schema` – tipos por columna y metainformación básica.
  - `missing_report` – %/conteo de faltantes por columna.
  - `profile` – estadísticas descriptivas con percentiles configurables.
  - `correlation` – matriz de correlación (pearson/spearman/kendall).
  - `detect_outliers` – detección por **IQR** o **Z-score**.
  - `groupby` – agregaciones por clave(s) con métricas parametrizables.
  - `export_report` – exporta reporte **md/json/html** a local o **Drive (carpeta)**.
- **CLI fallback** incluida (útil para depuración/uso directo).

---

## Requisitos
- **Python 3.10+** (recomendado 3.11).
- `pip`, `setuptools`, `wheel` actualizados.

### Instalación
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip setuptools wheel

# Instala el paquete en modo editable (usa pyproject.toml)
python -m pip install -e .

# Dependencias base (si no se instalaron automáticamente)
python -m pip install mcp pandas openpyxl "xlrd==1.2.0"

# (Opcional) extras para Google Drive/Sheets
python -m pip install "gspread>=6" "google-auth>=2.28" "google-auth-oauthlib>=1.2" "pydrive2>=1.19"
```
> Nota: `xlrd==1.2.0` se requiere solo para **.xls** antiguos. Para **.xlsx** se usa `openpyxl`.

---

## Credenciales Google (opcional)
### Service Account (SA) – acceso de lectura a Drive/Sheets
1. Crea una **Service Account** en Google Cloud y habilita **Drive API** y **Sheets API**.
2. Descarga la clave JSON a `secrets/sa.json` (no subir a git).
3. Exporta:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="$PWD/secrets/sa.json"
   ```
4. **Comparte** el **Sheet** y/o la **carpeta de Drive** con el **correo de la SA**.

### OAuth Desktop (para subir a *Mi unidad* o cuando SA no tiene permisos)
1. Configura **OAuth consent screen** (External) y agrega tu correo como **Test user**.
2. Crea un **OAuth Client ID** tipo **Desktop** y guarda `secrets/client_secret.json`.
3. (Opcional, para ruta explícita de token)
   ```bash
   export GOOGLE_OAUTH_CLIENT_SECRETS="secrets/client_secret.json"
   export GOOGLE_OAUTH_TOKEN="secrets/token.json"
   ```

---

## Uso como **CLI**
Ejecuta el modo consola:
```bash
python -m dataframe_analyst_mcp.server --cli
```
Comandos de ejemplo:
```text
# Cargar desde local
load_data {"source":{"type":"local","path":"examples/ventas_2023.csv"},"options":{"header":0}}

# Cargar desde Google Sheets (usa tu spreadsheetId)
load_data {"source":{"type":"gsheet","spreadsheetId":"<SPREADSHEET_ID>"},"options":{"header":0}}

# Cargar desde Google Drive (usa tu fileId de un CSV/XLSX/Sheet)
load_data {"source":{"type":"gdrive_file","fileId":"<FILE_ID>"},"options":{"header":0}}

infer_schema {}
missing_report {}
profile {"columns":["precio","cantidad"],"percentiles":[0.05,0.5,0.95]}
correlation {"method":"pearson"}
detect_outliers {"column":"precio","method":"iqr","factor":1.5}
groupby {"by":["categoria"],"metrics":{"precio":["mean","max"],"cantidad":["sum"]}}

# Exportar reporte a local
export_report {"dest":{"type":"local","path":"out/reporte.md"}, "fmt":"md", "sections":["schema","missing","profile","correlation"]}

# Exportar a Google Drive (carpeta)
export_report {"dest":{"type":"gdrive_folder","folderId":"<FOLDER_ID>"},"fmt":"md","sections":["schema","missing","profile","correlation"]}
```

---

## Uso como **MCP Server (STDIO)**
Arranque directo:
```bash
python -m dataframe_analyst_mcp.server --mcp
```

### Integración con clientes MCP (config ejemplo)
`mcpServers.json`:
```json
{
  "mcpServers": {
    "dataframe-analyst": {
      "command": "python",
      "args": ["-m", "dataframe_analyst_mcp.server", "--mcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/ruta/abs/secrets/sa.json",
        "GOOGLE_OAUTH_CLIENT_SECRETS": "/ruta/abs/secrets/client_secret.json",
        "GOOGLE_OAUTH_TOKEN": "/ruta/abs/secrets/token.json"
      }
    }
  }
}
```

### Smoke test (cliente Python mínimo)
```bash
python - <<'PY'
import asyncio, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CSV = "/Users/diederichsolis/Desktop/codigos/dataframe-analyst-mcp/examples/ventas_2023.csv"  # ajusta ruta si cambiaste el proyecto

async def main():
    params = StdioServerParameters(command="python", args=["-m","dataframe_analyst_mcp.server","--mcp"])
    async with stdio_client(params) as (r,w):
        async with ClientSession(r,w) as s:
            await s.initialize()

            # 1) Cargar datos
            await s.call_tool("load_data", {"source": {"type":"local","path": CSV}})

            # 2) Esquema
            r = await s.call_tool("infer_schema", {})
            print("infer_schema →", r.content[0].text[:240], "...\n")

            # 3) Perfil
            r = await s.call_tool("profile", {"percentiles":[0.05, 0.5, 0.95]})
            print("profile →", r.content[0].text[:240], "...\n")

            # 4) Correlación
            r = await s.call_tool("correlation", {"method":"pearson"})
            print("correlation →", r.content[0].text[:240], "...\n")

asyncio.run(main())
PY
```

---

## Estructura del proyecto
```
src/
  dataframe_analyst_mcp/
    __init__.py
    server.py            # FastMCP app (herramientas declaradas)
    state.py             # almacena el DataFrame en memoria de sesión
    tools/
      __init__.py
      loader.py
      schema.py
      missing.py
      profile.py
      corr.py
      outliers.py
      groupby.py
      export_report.py
examples/
  ventas_2023.csv
  ventas_2023.xlsx
  demo_script.md
out/                    # (se crea al exportar reportes locales)
secrets/                # credenciales (ignorar en git)
pyproject.toml
README.md
```

---

## Solución de problemas
- **No se encuentra el módulo**: ejecuta `python -m pip install -e .` en la raíz del repo y verifica que `src/` contenga `dataframe_analyst_mcp/`.
- **Importa pero no conecta por STDIO**: prueba `PYTHONPATH=src python -m dataframe_analyst_mcp.server --mcp`.
- **403/404 en Drive/Sheets**: comparte recursos con el correo de la **Service Account** o usa **OAuth Desktop** (ver arriba).
- **`xlrd` y archivos `.xls`**: solo es compatible `xlrd==1.2.0`. Para `.xlsx` usa `openpyxl`.
- **Correlación con 0s**: las columnas no numéricas se muestran como 0; limita a numéricas si lo deseas en tu reporte.

