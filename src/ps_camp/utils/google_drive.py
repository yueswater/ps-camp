from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

import os
import pickle
import io
import logging

# 授權範圍：只要能上傳就好
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# 憑證與 token 路徑
CREDENTIALS_FILE = 'client_secret_1020131056840-30cishu970m00bg44st3t4n0cpvek4sl.apps.googleusercontent.com.json'
TOKEN_FILE = 'token_drive.pkl'

# 指定上傳的 Google Drive 資料夾 ID
FOLDER_ID = '1zkbES2XtbK6xXglTInCuTn7wmk882XHO'


def get_drive_service():
    """取得 Google Drive API 的 service 實體"""
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError("找不到 token_drive.pkl，請先本地授權產生一次。")

    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        else:
            raise RuntimeError("token 無效且無法刷新，請重新手動授權。")

    return build('drive', 'v3', credentials=creds)


def upload_file_to_drive(file_storage, filename: str, mimetype: str = None) -> str:
    """將檔案上傳至 Google Drive 並取得可分享的連結"""
    service = get_drive_service()

    file_metadata = {
        'name': filename,
        'parents': [FOLDER_ID]
    }

    file_stream = io.BytesIO(file_storage.read())
    media = MediaIoBaseUpload(file_stream, mimetype or file_storage.mimetype)

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    service.permissions().create(
        fileId=uploaded_file['id'],
        body={"role": "reader", "type": "anyone"},
    ).execute()

    return f"https://drive.google.com/file/d/{uploaded_file['id']}/view"
