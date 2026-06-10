import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration
SERVICE_ACCOUNT_FILE = '../account/service-account.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] # Lecture seule pour le test
PARENT_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')

def get_drive_service():
    """Initialise le service Google Drive avec le compte de service."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Le fichier {SERVICE_ACCOUNT_FILE} est introuvable.")
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def test_connection():
    """Teste la connexion et liste les fichiers du dossier configuré."""
    if not PARENT_FOLDER_ID:
        print("Erreur : DRIVE_FOLDER_ID n'est pas défini dans le fichier .env")
        return

    try:
        service = get_drive_service()
        print(f"Connexion réussie. Vérification du dossier ID : {PARENT_FOLDER_ID}")
        
        # Essayer de lister les fichiers dans le dossier pour valider l'accès
        query = f"'{PARENT_FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(
            q=query, 
            fields="nextPageToken, files(id, name)",
            pageSize=10
        ).execute()
        
        items = results.get('files', [])

        if not items:
            print('Dossier trouvé, mais il est vide ou vous n\'avez pas encore partagé de fichiers avec le compte de service.')
        else:
            print('Connexion validée ! Fichiers trouvés dans le dossier :')
            for item in items:
                print(f" - {item['name']} ({item['id']})")
                
    except HttpError as error:
        if error.resp.status == 404:
            print(f"Erreur 404 : Le dossier avec l'ID '{PARENT_FOLDER_ID}' est introuvable. Vérifiez l'ID dans votre fichier .env.")
        elif error.resp.status == 403:
            print(f"Erreur 403 : Accès refusé. Avez-vous partagé le dossier avec l'email du compte de service ?")
        else:
            print(f"Une erreur Google Drive est survenue : {error}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

if __name__ == '__main__':
    test_connection()
