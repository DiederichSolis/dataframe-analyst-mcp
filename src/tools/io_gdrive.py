from __future__ import annotations
import os, io, tempfile, mimetypes
from typing import Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

# 👇 NUEVO: OAuth de usuario
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GRequest
import json

DRIVE_SCOPE_RW = ("https://www.googleapis.com/auth/drive",)
DRIVE_SCOPE_RO = ("https://www.googleapis.com/auth/drive.readonly",)

def _drive_service_sa(scopes=DRIVE_SCOPE_RW):
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not sa_path or not os.path.exists(sa_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set or invalid.")
    creds = Credentials.from_service_account_file(sa_path, scopes=list(scopes))
    return build("drive", "v3", credentials=creds)

def _drive_service_oauth(scopes=DRIVE_SCOPE_RW):
    client_file = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "secrets/client_secret.json")
    token_file  = os.environ.get("GOOGLE_OAUTH_TOKEN", "secrets/token.json")

    creds = None
    if os.path.exists(token_file):
        creds = UserCredentials.from_authorized_user_file(token_file, list(scopes))
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_file, list(scopes))
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def download_file_to_tmp(file_id: str) -> str:
    # lectura: con SA basta (puedes cambiar a _drive_service_oauth si prefieres)
    svc = _drive_service_sa(scopes=DRIVE_SCOPE_RO)
    meta = svc.files().get(fileId=file_id, fields="id,name,mimeType").execute()
    mime = meta["mimeType"]; name = meta["name"]

    if mime == "application/vnd.google-apps.spreadsheet":
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        request = svc.files().export_media(fileId=file_id, mimeType="text/csv")
        with io.FileIO(tmp.name, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return tmp.name

    ext = os.path.splitext(name)[1] or (mimetypes.guess_extension(mime) or ".bin")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    request = svc.files().get_media(fileId=file_id)
    with io.FileIO(tmp.name, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return tmp.name

def upload_bytes_to_drive(folder_id: str, filename: str, content: bytes,
                          mime: str = "text/plain", overwrite: bool = True) -> Dict:
    """
    Intenta subir con Service Account; si da 403 storageQuotaExceeded,
    hace fallback a OAuth de usuario (Desktop) y vuelve a subir.
    Soporta Mi unidad y Unidades compartidas.
    """
    def _do_upload(svc):
        # borrar si overwrite
        if overwrite:
            q = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
            existing = svc.files().list(
                q=q, fields="files(id)",
                includeItemsFromAllDrives=True, supportsAllDrives=True
            ).execute().get("files", [])
            for f in existing:
                svc.files().delete(fileId=f["id"]).execute()

        metadata = {"name": filename, "parents": [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime, resumable=True)
        newf = svc.files().create(
            body=metadata, media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True
        ).execute()
        return {"fileId": newf["id"], "webViewLink": newf.get("webViewLink")}

    # 1) intenta con Service Account
    try:
        svc_sa = _drive_service_sa(scopes=DRIVE_SCOPE_RW)
        return _do_upload(svc_sa)
    except HttpError as e:
        # 403 sin cuota de SA ⇒ fallback a OAuth del usuario
        if e.resp.status == 403 and "storageQuotaExceeded" in str(e):
            svc_user = _drive_service_oauth(scopes=DRIVE_SCOPE_RW)
            return _do_upload(svc_user)
        raise
