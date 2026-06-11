import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_DIR = os.path.normpath(os.path.join(BASE_DIR, '../account'))
SERVICE_ACCOUNT_FILE = os.path.join(ACCOUNT_DIR, 'service-account.json')
CLIENT_SECRET_FILE = os.path.join(ACCOUNT_DIR, 'client-secret.json')
TOKEN_FILE = os.path.join(ACCOUNT_DIR, 'token.json')

SCOPES = ['https://www.googleapis.com/auth/drive'] 
PARENT_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')
