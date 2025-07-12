import os, base64, pickle, io
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token_drive.pkl'
FOLDER_ID = '1zkbES2XtbK6xXglTInCuTn7wmk882XHO'

def restore_token_from_env():
    if os.path.exists(TOKEN_FILE): return
    b64 = os.getenv("GOOGLE_TOKEN_B64")
    if not b64: raise RuntimeError("環境變數 GOOGLE_TOKEN_B64 不存在")
    with open(TOKEN_FILE, "wb") as f:
        f.write(base64.b64decode(b64))

def get_drive_service():
    restore_token_from_env()
    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "wb") as f2:
                pickle.dump(creds, f2)
        else:
            raise RuntimeError("token 無效且無法刷新")
    return build("drive", "v3", credentials=creds)

def upload_file_to_drive(file_storage, filename: str, mimetype: str = None) -> str:
    service = get_drive_service()
    metadata = {'name': filename, 'parents': [FOLDER_ID]}
    stream = io.BytesIO(file_storage.read())
    media = MediaIoBaseUpload(stream, mimetype or file_storage.mimetype)
    file = service.files().create(body=metadata, media_body=media, fields="id").execute()
    service.permissions().create(fileId=file["id"], body={"role": "reader", "type": "anyone"}).execute()
    return f"https://drive.google.com/file/d/{file['id']}/view"
