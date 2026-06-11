import os
import argparse
import mimetypes
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_DIR = os.path.join(BASE_DIR, '../account')
SERVICE_ACCOUNT_FILE = os.path.join(ACCOUNT_DIR, 'service-account.json')
CLIENT_SECRET_FILE = os.path.join(ACCOUNT_DIR, 'client-secret.json')
TOKEN_FILE = os.path.join(ACCOUNT_DIR, 'token.json')

SCOPES = ['https://www.googleapis.com/auth/drive'] 
PARENT_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')

def get_drive_service(headless=False):
    """Initialise le service Google Drive avec les identifiants utilisateur (OAuth2) ou compte de service."""
    creds = None
    
    # 1. Essayer de charger les identifiants utilisateur (OAuth2)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Si pas d'identifiants valides, on lance le flux de connexion
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(CLIENT_SECRET_FILE):
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            if headless:
                # Mode console pour les serveurs distants
                creds = flow.run_console()
            else:
                # Mode local avec ouverture de navigateur
                creds = flow.run_local_server(port=0)
            
            # Sauvegarder les identifiants pour la prochaine fois
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        else:
            # 2. Repli vers le compte de service si OAuth2 n'est pas configuré
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                print("Note: Utilisation du compte de service (attention au quota de stockage).")
                creds = service_account.Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            else:
                raise FileNotFoundError(
                    f"Aucun identifiant trouvé. Veuillez placer 'client-secret.json' ou "
                    f"'service-account.json' dans le dossier {ACCOUNT_DIR}"
                )
    
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name, parent_id=None):
    """Recherche un dossier par son nom ou le crée s'il n'existe pas."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    try:
        results = service.files().list(
            q=query, 
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = service.files().create(
                body=file_metadata, 
                fields='id',
                supportsAllDrives=True
            ).execute()
            print(f"Dossier créé : {folder_name}")
            return folder.get('id')
    except HttpError as error:
        print(f"Une erreur est survenue lors de la gestion du dossier '{folder_name}': {error}")
        return None

def upload_file(service, local_path, parent_id):
    """Télécharge un fichier vers Google Drive."""
    file_name = os.path.basename(local_path)
    
    query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
    try:
        results = service.files().list(
            q=query, 
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
        
        mime_type, _ = mimetypes.guess_type(local_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
            
        media = MediaFileUpload(local_path, mimetype=mime_type)
        
        if items:
            file_id = items[0]['id']
            service.files().update(
                fileId=file_id, 
                media_body=media,
                supportsAllDrives=True
            ).execute()
            print(f"Fichier mis à jour : {file_name}")
        else:
            file_metadata = {
                'name': file_name,
                'parents': [parent_id]
            }
            service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id',
                supportsAllDrives=True
            ).execute()
            print(f"Fichier importé : {file_name}")
    except HttpError as error:
        if error.resp.status == 403 and "storageQuotaExceeded" in str(error):
            print(f"Erreur : Quota de stockage dépassé.")
            print("Conseil : Utilisez l'authentification OAuth2 (User) au lieu d'un compte de service.")
            print(f"Placez le fichier 'client-secret.json' dans {ACCOUNT_DIR} pour activer OAuth2.")
        else:
            print(f"Une erreur est survenue lors de l'importation de '{file_name}': {error}")

def sync_verse(service, data_path, book, chapter, verse, parent_folder_id):
    """Synchronise un verset spécifique."""
    print(f"Synchronisation du verset : {verse} ({book}/{chapter})")
    
    lang_folder_name = os.path.basename(data_path)
    lang_id = get_or_create_folder(service, lang_folder_name, parent_folder_id)
    book_id = get_or_create_folder(service, book, lang_id)
    chapter_id = get_or_create_folder(service, chapter, book_id)
    verse_id = get_or_create_folder(service, verse, chapter_id)
    
    verse_local_path = os.path.join(data_path, book, chapter, verse)
    if not os.path.isdir(verse_local_path):
        print(f"Erreur : Le dossier du verset '{verse_local_path}' est introuvable.")
        return

    for file in os.listdir(verse_local_path):
        file_path = os.path.join(verse_local_path, file)
        if os.path.isfile(file_path):
            upload_file(service, file_path, verse_id)

def sync_chapter(service, data_path, book, chapter, parent_folder_id):
    """Synchronise un chapitre entier."""
    print(f"Synchronisation du chapitre : {chapter} ({book})")
    
    lang_folder_name = os.path.basename(data_path)
    lang_id = get_or_create_folder(service, lang_folder_name, parent_folder_id)
    book_id = get_or_create_folder(service, book, lang_id)
    chapter_id = get_or_create_folder(service, chapter, book_id)
    
    chapter_local_path = os.path.join(data_path, book, chapter)
    if not os.path.isdir(chapter_local_path):
        print(f"Erreur : Le dossier du chapitre '{chapter_local_path}' est introuvable.")
        return

    for item in os.listdir(chapter_local_path):
        item_path = os.path.join(chapter_local_path, item)
        if os.path.isfile(item_path):
            upload_file(service, item_path, chapter_id)
        elif os.path.isdir(item_path) and item.startswith('V_'):
            sync_verse(service, data_path, book, chapter, item, parent_folder_id)

def sync_book(service, data_path, book, parent_folder_id):
    """Synchronise un livre entier."""
    print(f"Synchronisation du livre : {book}")
    
    book_local_path = os.path.join(data_path, book)
    if not os.path.isdir(book_local_path):
        print(f"Erreur : Le dossier du livre '{book_local_path}' est introuvable.")
        return

    for chapter in os.listdir(book_local_path):
        chapter_path = os.path.join(book_local_path, chapter)
        if os.path.isdir(chapter_path) and chapter.startswith(f"{book}_"):
            sync_chapter(service, data_path, book, chapter, parent_folder_id)

def main():
    parser = argparse.ArgumentParser(description='Synchronise les données locales avec Google Drive.')
    parser.add_argument(
        '--data_folder',
        type=str,
        default='../scraping/data/ewondo',
        help='Chemin vers le dossier de données local.'
    )
    parser.add_argument(
        '--book',
        type=str,
        help='Livre spécifique à synchroniser (ex: MAT).'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        help='Chapitre spécifique à synchroniser (ex: MAT_1).'
    )
    parser.add_argument(
        '--verse',
        type=str,
        help='Verset spécifique à synchroniser (ex: V_1).'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Utiliser le mode console pour l\'authentification (utile pour les serveurs distants).'
    )
    
    args = parser.parse_args()
    
    if not PARENT_FOLDER_ID:
        print("Erreur : DRIVE_FOLDER_ID n'est pas défini dans le fichier .env")
        return

    try:
        service = get_drive_service(headless=args.headless)
        
        if not os.path.isabs(args.data_folder):
            data_path = os.path.join(BASE_DIR, args.data_folder)
        else:
            data_path = args.data_folder
            
        data_path = os.path.normpath(data_path)

        if args.verse:
            if not args.book or not args.chapter:
                parser.error("--book et --chapter sont requis quand --verse est spécifié.")
            sync_verse(service, data_path, args.book, args.chapter, args.verse, PARENT_FOLDER_ID)
        elif args.chapter:
            if not args.book:
                parser.error("--book est requis quand --chapter est spécifié.")
            sync_chapter(service, data_path, args.book, args.chapter, PARENT_FOLDER_ID)
        elif args.book:
            sync_book(service, data_path, args.book, PARENT_FOLDER_ID)
        else:
            parser.error("Vous devez spécifier au moins --book.")
            
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

if __name__ == '__main__':
    main()
