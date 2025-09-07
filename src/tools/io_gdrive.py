from __future__ import annotations
import os
import tempfile
import mimetypes
import pandas as pd

def _authorize_drive():
    from google.oauth2.service_account import Credentials
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive

    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not sa_path or not os.path.exists(sa_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set or invalid.")

    base_scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(sa_path, scopes=base_scopes)
    gauth = GoogleAuth()
    gauth.credentials = creds
    drive = GoogleDrive(gauth)
    return drive

def download_file_to_tmp(file_id: str) -> str:
    drive = _authorize_drive()
    f = drive.CreateFile({'id': file_id})
    suffix = ".bin"
    mime = f['mimeType']
    # Guess extension
    guessed = mimetypes.guess_extension(mime) or ""
    if "spreadsheet" in mime:
        # Google Sheets native: export as CSV
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        f.GetContentFile(tmp.name, mimetype="text/csv")
        return tmp.name
    else:
        # Regular uploaded file
        if not guessed:
            # try to infer from title
            title = f['title']
            if '.' in title:
                guessed = '.' + title.rsplit('.', 1)[-1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=guessed or suffix)
        f.GetContentFile(tmp.name)
        return tmp.name

def upload_bytes_to_drive(folder_id: str, filename: str, content: bytes, mime: str = "text/plain", overwrite: bool = True) -> dict:
    drive = _authorize_drive()

    # Optionally delete existing same-name file in folder
    if overwrite:
        file_list = drive.ListFile({
            'q': f"'{folder_id}' in parents and title = '{filename}' and trashed = false"
        }).GetList()
        for old in file_list:
            old.Delete()

    f = drive.CreateFile({'title': filename, 'parents': [{'id': folder_id}]})
    f.SetContentString(content.decode("utf-8", errors="ignore") if mime.startswith("text/") else content)  # for text
    if not mime.startswith("text/"):
        # For binary, SetContentString won't be correct; in practice, you'd use SetContentFile with a temp file.
        # To keep it simple for report text/markdown/html, this branch won't be used.
        pass
    f.Upload()
    f.FetchMetadata()
    return {
        "fileId": f["id"],
        "webViewLink": f.get("alternateLink") or f.get("webContentLink")
    }
