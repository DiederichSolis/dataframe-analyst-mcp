# dataframe-analyst-mcp

Servidor **MCP** (y CLI) para analizar datasets (**CSV/XLS/XLSX/Google Sheets/Google Drive**) y exportar reportes (**md/json/html**) a **local** o **Google Drive**.

## Características
- Carga desde: local (`path`), **Drive** (`fileId`), **Sheets** (`spreadsheetId`).
- Herramientas: `infer_schema`, `missing_report`, `profile` (con `p25/p50/p75`), `correlation`, `detect_outliers`, `groupby`.
- Exporta reportes a **local** o **Drive** (`folderId`).

---

## Requisitos
- **Python 3.11** (recomendado)
- Dependencias: `pandas`, `openpyxl`, `xlrd==1.2.0`, `gspread`, `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `pydrive2`.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install pandas openpyxl "xlrd==1.2.0" gspread google-auth google-auth-oauthlib google-api-python-client pydrive2
```

---

## Credenciales
### Service Account (SA) – lectura y acceso a Sheets/Drive
1. Crea una **Service Account** en Google Cloud, habilita **Drive API** y **Sheets API**.
2. Descarga la key JSON en `secrets/sa.json` (no subir a git).
3. Exporta la variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/secrets/sa.json"
```
4. **Comparte** tu **Sheet** y **carpeta de Drive** con el **correo** de la SA (con `@`).

### OAuth Desktop (fallback para subir a *Mi unidad*)
Las SA no tienen cuota en *Mi unidad*. Para subir, el servidor usa *fallback* OAuth:
1. En **OAuth consent screen**: tipo **External** y agrega tu correo en **Test users**.
2. Crea **OAuth Client ID** tipo **Desktop** y guarda `secrets/client_secret.json`.
3. (Opcional)
```bash
export GOOGLE_OAUTH_CLIENT_SECRETS="secrets/client_secret.json"
export GOOGLE_OAUTH_TOKEN="secrets/token.json"
```
> La primera subida abrirá el navegador y guardará `token.json`.

---

## Uso rápido (CLI)
```bash
python -m src.server --cli
```
Ejemplos de comandos:
```text
# Local
load_data {"source":{"type":"local","path":"examples/ventas_2023.csv"},"options":{"header":0}}

# Sheets (spreadsheetId real)
load_data {"source":{"type":"gsheet","spreadsheetId":"<SPREADSHEET_ID>"},"options":{"header":0}}

# Drive (fileId real de un CSV/XLSX o Sheet)
load_data {"source":{"type":"gdrive_file","fileId":"<FILE_ID>"},"options":{"header":0}}

infer_schema {}
missing_report {}
profile {"columns":["precio","cantidad"],"percentiles":[0.25,0.5,0.75]}
correlation {"method":"pearson"}
detect_outliers {"column":"precio","method":"iqr","factor":1.5}
groupby {"by":["categoria"],"metrics":{"precio":["mean","max"],"cantidad":["sum"]}}

# Export local
export_report {"dest":{"type":"local","path":"out/reporte.md"},"format":"md","sections":["schema","missing","profile","outliers","corr"]}

# Export a Drive (folderId real)
export_report {"dest":{"type":"gdrive","folderId":"<FOLDER_ID>","filename":"reporte.md","mime":"text/markdown","overwrite":true},"format":"md","sections":["schema","missing","profile","outliers","corr"]}
```

---

## Modo MCP (STDIO)
Configura tu host/cliente MCP para lanzar el server por stdio:
```json
{
  "mcpServers": {
    "dataframe-analyst": {
      "command": "python",
      "args": ["-m", "src.server", "--mcp"],
      "cwd": "/ruta/absoluta/a/dataframe-analyst-mcp",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/ruta/abs/secrets/sa.json",
        "GOOGLE_OAUTH_CLIENT_SECRETS": "/ruta/abs/secrets/client_secret.json",
        "GOOGLE_OAUTH_TOKEN": "/ruta/abs/secrets/token.json"
      }
    }
  }
}
```

---

## Solución de problemas
- **403 insufficientPermissions** → Comparte Sheet/carpeta con el **correo de la SA**.
- **404 notFound** → Revisa `fileId`/`folderId`/`spreadsheetId` y permisos.
- **403 storageQuotaExceeded (SA)** → Sube con **OAuth Desktop** (ya soportado como fallback) o usa **Unidad compartida**.
- **App no verificada / access_denied (OAuth)** → En **OAuth consent screen** usa **External**, agrega tu correo como **Test user** y añade scopes (`drive.file` o `drive`).
- **Worksheet not found (XLSX)** → Usa `"sheet":0` o el nombre exacto de la hoja.

---



