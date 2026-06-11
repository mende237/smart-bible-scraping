import os
import logging
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
try:
    from config import TOKEN_FILE, CLIENT_SECRET_FILE, SERVICE_ACCOUNT_FILE, SCOPES, ACCOUNT_DIR
except ImportError:
    from .config import TOKEN_FILE, CLIENT_SECRET_FILE, SERVICE_ACCOUNT_FILE, SCOPES, ACCOUNT_DIR

def get_drive_service(headless: bool = False):
    """Initializes the Google Drive service."""
    creds = None
    
    # 1. Try OAuth2
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(CLIENT_SECRET_FILE):
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_console() if headless else flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        elif os.path.exists(SERVICE_ACCOUNT_FILE):
            logging.info("Using service account (limited storage).")
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        else:
            raise FileNotFoundError(f"Credentials not found in {ACCOUNT_DIR}")
    
    return build('drive', 'v3', credentials=creds)
