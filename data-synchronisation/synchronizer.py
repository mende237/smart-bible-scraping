import os
import mimetypes
import subprocess
import sys
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
try:
    from auth import get_drive_service
except ImportError:
    from .auth import get_drive_service

class DataSynchronizer:
    def __init__(self, headless: bool = False):
        self.service = get_drive_service(headless)
        self.failures: Dict[str, Dict[str, List[str]]] = {}
        self.enable_date_check: bool = True

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Finds or creates a folder on Google Drive."""
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        try:
            results = self.service.files().list(
                q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            
            file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
            logging.info(f"Folder created: {folder_name}")
            return folder.get('id')
        except HttpError as error:
            logging.error(f"Error managing folder '{folder_name}': {error}")
            return None

    def get_file_id(self, file_name: str, parent_id: str) -> Optional[str]:
        """Finds a file ID on Google Drive by name and parent ID."""
        query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
        try:
            results = self.service.files().list(
                q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            items = results.get('files', [])
            return items[0]['id'] if items else None
        except HttpError as error:
            logging.error(f"Error checking file existence for '{file_name}': {error}")
            return None

    def create_file(self, local_path: str, parent_id: str, media: MediaFileUpload) -> Optional[str]:
        """Creates a new file on Google Drive."""
        file_name = os.path.basename(local_path)
        file_metadata = {'name': file_name, 'parents': [parent_id]}
        try:
            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
            ).execute()
            logging.info(f"File imported: {file_name}")
            return file.get('id')
        except HttpError as error:
            self._handle_upload_error(file_name, error)
            return None

    def update_file(self, local_path: str, file_id: str, media: MediaFileUpload):
        """Updates an existing file on Google Drive."""
        file_name = os.path.basename(local_path)
        try:
            self.service.files().update(
                fileId=file_id, media_body=media, supportsAllDrives=True
            ).execute()
            logging.info(f"File updated: {file_name}")
        except HttpError as error:
            self._handle_upload_error(file_name, error)

    def _handle_upload_error(self, file_name: str, error: HttpError):
        """Helper to handle HTTP errors during upload/update operations."""
        if error.resp.status == 403 and "storageQuotaExceeded" in str(error):
            logging.error("Storage quota exceeded. Consider switching to OAuth2.")
        else:
            logging.error(f"Error importing/updating '{file_name}': {error}")

    def _get_remote_modified_time(self, file_id: str) -> Optional[datetime]:
        """Returns the last modified time of a Google Drive file as a UTC datetime."""
        try:
            result = self.service.files().get(
                fileId=file_id,
                fields='modifiedTime',
                supportsAllDrives=True
            ).execute()
            remote_modified_time = result.get('modifiedTime')
            if not remote_modified_time:
                return None

            if remote_modified_time.endswith('Z'):
                remote_modified_time = remote_modified_time[:-1] + '+00:00'

            return datetime.fromisoformat(remote_modified_time).astimezone(timezone.utc)
        except Exception as error:
            logging.warning(f"Unable to read modified time for file '{file_id}': {error}")
            return None

    def _should_skip_upload(self, local_path: str, file_id: str) -> bool:
        """Returns True when the remote file is already up to date or newer."""
        if not file_id:
            return False

        local_modified_time = datetime.fromtimestamp(os.path.getmtime(local_path), tz=timezone.utc)
        remote_modified_time = self._get_remote_modified_time(file_id)

        if remote_modified_time is None:
            return False

        return remote_modified_time >= local_modified_time

    def upload_file(self, local_path: str, parent_id: str):
        """Uploads or updates a file on Google Drive."""
        file_name = os.path.basename(local_path)
        file_id = self.get_file_id(file_name, parent_id)
        
        if file_id and self.enable_date_check and self._should_skip_upload(local_path, file_id):
            logging.info(f"Skipping upload for '{file_name}' because the Drive copy is up to date.")
            return

        try:
            mime_type, _ = mimetypes.guess_type(local_path)
            media = MediaFileUpload(local_path, mimetype=mime_type or 'application/octet-stream')
            
            if file_id:
                self.update_file(local_path, file_id, media)
            else:
                self.create_file(local_path, parent_id, media)
        except Exception as e:
            logging.error(f"Failed to prepare media upload for '{file_name}': {e}")

    def run_verification(self, data_path: str, book: str = None, chapter: str = None, verse: str = None, preprocessor: str = None, books: List[str] = None, chapters: List[str] = None) -> bool:
        """Runs the external verification script and captures failures."""
        logging.info("="*50)
        logging.info("STARTING DATA VERIFICATION")
        logging.info("="*50)
        
        script_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data-verification', 'verify_data.py'))
        cmd = [sys.executable, script_path, '--data_folder', data_path, '--json']
        if preprocessor: cmd.extend(['--preprocessor', preprocessor])
        elif books: cmd.extend(['--books'] + books)
        elif verse: cmd.extend(['--book', book, '--chapter', chapter, '--verse', verse])
        elif chapters: cmd.extend(['--book', book, '--chapters'] + chapters)
        elif chapter: cmd.extend(['--book', book, '--chapter', chapter])
        elif book: cmd.extend(['--book', book])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = result.stdout
            
            # Extract JSON from output
            if "---JSON_START---" in output:
                try:
                    json_str = output.split("---JSON_START---")[1].split("---JSON_END---")[0].strip()
                    report = json.loads(json_str)
                    self.failures = report.get("failures", {})
                    if report.get("failed"):
                        logging.warning("Verification found issues. Some items will be skipped during synchronization.")
                    else:
                        logging.info("Data verification successful.\n")
                    return True # Continue with partial sync
                except (IndexError, json.JSONDecodeError) as e:
                    logging.error(f"Failed to parse verification report: {e}")
                    return False
            else:
                if result.returncode != 0:
                    logging.error(f"Verification failed without JSON output. Stderr: {result.stderr}")
                    return False
                logging.info("Data verification successful (no failures reported).\n")
                return True
        except Exception as e:
            logging.error(f"Verification execution error: {e}")
            return False

    def is_failed(self, book: str, chapter: str = None, verse: str = None) -> bool:
        """Checks if a specific item failed verification."""
        if book not in self.failures:
            return False
        
        chapter_failures = self.failures[book]
        if chapter is None:
            return False 

        if chapter not in chapter_failures:
            return False
            
        verse_failures = chapter_failures[chapter]
        if verse is None:
            # If the chapter text itself is missing or failed (usually represented as an empty list or specific error)
            return False
            
        return verse in verse_failures

    def sync_preprocessor(self, data_path: str, preprocessor_name: str, parent_id: str):
        """Synchronizes all tasks assigned to a specific preprocessor."""
        assignment_file = os.path.join(data_path, "assignment.json")
        
        if not os.path.exists(assignment_file):
            logging.error(f"Assignment file not found: {assignment_file}")
            return

        with open(assignment_file, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
            
        if preprocessor_name not in assignments:
            logging.error(f"Preprocessor '{preprocessor_name}' not found in assignment file.")
            return
            
        preprocessor_tasks = assignments[preprocessor_name]
        logging.info(f"Syncing all tasks for preprocessor: {preprocessor_name}")

        for book, chapters in preprocessor_tasks.items():
            if book == "total_duration_hours":
                continue
                
            if chapters == "all":
                self.sync_book(data_path, book, parent_id)
            else:
                book_id = self.get_or_create_folder(book, parent_id)
                if not book_id: continue
                for chapter in chapters:
                    self.sync_chapter(data_path, book, chapter, book_id)

    def sync_verse(self, data_path: str, book: str, chapter: str, verse: str, parent_id: str):
        """Synchronizes a single verse."""
        if self.is_failed(book, chapter, verse):
            logging.warning(f"Skipping verse {verse} ({book}/{chapter}) due to verification failure.")
            return

        logging.info(f"Syncing verse: {verse} ({book}/{chapter})")
        verse_id = self.get_or_create_folder(verse, parent_id)
        if not verse_id: return

        verse_local_path = os.path.join(data_path, book, chapter, verse)
        if not os.path.isdir(verse_local_path):
            logging.error(f"Verse folder '{verse_local_path}' not found.")
            return

        for file in os.listdir(verse_local_path):
            file_path = os.path.join(verse_local_path, file)
            if os.path.isfile(file_path):
                self.upload_file(file_path, verse_id)

    def sync_chapter(self, data_path: str, book: str, chapter: str, parent_id: str):
        """Synchronizes a single chapter."""
        logging.info(f"Syncing chapter: {chapter} ({book})")
        chapter_id = self.get_or_create_folder(chapter, parent_id)
        if not chapter_id: return

        chapter_local_path = os.path.join(data_path, book, chapter)
        if not os.path.isdir(chapter_local_path):
            logging.error(f"Chapter folder '{chapter_local_path}' not found.")
            return

        for item in os.listdir(chapter_local_path):
            item_path = os.path.join(chapter_local_path, item)
            if os.path.isfile(item_path):
                self.upload_file(item_path, chapter_id)
            elif os.path.isdir(item_path) and item.startswith('V_'):
                self.sync_verse(data_path, book, chapter, item, chapter_id)

    def sync_book(self, data_path: str, book: str, parent_id: str):
        """Synchronizes an entire book."""
        logging.info(f"Syncing book: {book}")
        book_id = self.get_or_create_folder(book, parent_id)
        if not book_id: return

        book_local_path = os.path.join(data_path, book)
        if not os.path.isdir(book_local_path):
            logging.error(f"Book folder '{book_local_path}' not found.")
            return

        for chapter in os.listdir(book_local_path):
            chapter_path = os.path.join(book_local_path, chapter)
            if os.path.isdir(chapter_path) and chapter.startswith(f"{book}_"):
                self.sync_chapter(data_path, book, chapter, book_id)

    def sync_books(self, data_path: str, books: List[str], parent_id: str):
        """Synchronizes multiple books."""
        logging.info(f"Syncing books: {', '.join(books)}")
        for book in books:
            self.sync_book(data_path, book, parent_id)

    def sync_chapters(self, data_path: str, book: str, chapters: List[str], parent_id: str):
        """Synchronizes multiple chapters."""
        logging.info(f"Syncing chapters: {', '.join(chapters)} for book {book}")
        for chapter in chapters:
            self.sync_chapter(data_path, book, chapter, parent_id)

    def get_folder_id(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Finds a folder on Google Drive without creating it."""
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        try:
            results = self.service.files().list(
                q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            items = results.get('files', [])
            if items:
                return items[0]['id']
            return None
        except HttpError as error:
            logging.error(f"Error finding folder '{folder_name}': {error}")
            return None

    def list_folder_contents(self, folder_id: str) -> List[Dict]:
        """Lists all files and folders inside a given Google Drive folder."""
        query = f"'{folder_id}' in parents and trashed = false"
        try:
            results = self.service.files().list(
                q=query, fields="files(id, name, mimeType)", supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            return results.get('files', [])
        except HttpError as error:
            logging.error(f"Error listing folder contents: {error}")
            return []

    def download_file(self, file_id: str, local_path: str):
        """Downloads a file from Google Drive."""
        from googleapiclient.http import MediaIoBaseDownload
        import io
        
        file_name = os.path.basename(local_path)
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            request = self.service.files().get_media(fileId=file_id)
            with io.FileIO(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            logging.info(f"File downloaded: {file_name}")
        except HttpError as error:
            logging.error(f"Error downloading '{file_name}': {error}")

    def download_verse(self, local_data_path: str, book: str, chapter: str, verse: str, parent_id: str):
        """Downloads files for a single verse from Google Drive."""
        logging.info(f"Downloading verse: {verse} ({book}/{chapter})")
        verse_id = self.get_folder_id(verse, parent_id)
        if not verse_id:
            logging.warning(f"Verse folder '{verse}' not found on Google Drive under parent {parent_id}.")
            return

        verse_local_path = os.path.join(local_data_path, book, chapter, verse)
        os.makedirs(verse_local_path, exist_ok=True)

        items = self.list_folder_contents(verse_id)
        for item in items:
            if item['mimeType'] != 'application/vnd.google-apps.folder':
                local_file_path = os.path.join(verse_local_path, item['name'])
                self.download_file(item['id'], local_file_path)

    def download_chapter(self, local_data_path: str, book: str, chapter: str, parent_id: str):
        """Downloads a single chapter."""
        logging.info(f"Downloading chapter: {chapter} ({book})")
        chapter_id = self.get_folder_id(chapter, parent_id)
        if not chapter_id:
            logging.warning(f"Chapter folder '{chapter}' not found on Google Drive.")
            return

        chapter_local_path = os.path.join(local_data_path, book, chapter)
        os.makedirs(chapter_local_path, exist_ok=True)

        items = self.list_folder_contents(chapter_id)
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                if item['name'].startswith('V_'):
                    self.download_verse(local_data_path, book, chapter, item['name'], chapter_id)
            else:
                local_file_path = os.path.join(chapter_local_path, item['name'])
                self.download_file(item['id'], local_file_path)

    def download_book(self, local_data_path: str, book: str, parent_id: str):
        """Downloads an entire book."""
        logging.info(f"Downloading book: {book}")
        book_id = self.get_folder_id(book, parent_id)
        if not book_id:
            logging.warning(f"Book folder '{book}' not found on Google Drive.")
            return

        book_local_path = os.path.join(local_data_path, book)
        os.makedirs(book_local_path, exist_ok=True)

        items = self.list_folder_contents(book_id)
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                if item['name'].startswith(f"{book}_"):
                    self.download_chapter(local_data_path, book, item['name'], book_id)
            else:
                local_file_path = os.path.join(book_local_path, item['name'])
                self.download_file(item['id'], local_file_path)

    def download_books(self, local_data_path: str, books: List[str], parent_id: str):
        """Downloads multiple books."""
        logging.info(f"Downloading books: {', '.join(books)}")
        for book in books:
            self.download_book(local_data_path, book, parent_id)

    def download_chapters(self, local_data_path: str, book: str, chapters: List[str], parent_id: str):
        """Downloads multiple chapters."""
        logging.info(f"Downloading chapters: {', '.join(chapters)} for book {book}")
        for chapter in chapters:
            self.download_chapter(local_data_path, book, chapter, parent_id)

    def download_preprocessor(self, local_data_path: str, preprocessor_name: str, parent_id: str):
        """Downloads all tasks assigned to a specific preprocessor."""
        assignment_file = os.path.join(local_data_path, "assignment.json")
        
        if not os.path.exists(assignment_file):
            logging.info("Assignment file not found locally. Searching on Google Drive...")
            assignment_query = f"name = 'assignment.json' and '{parent_id}' in parents and trashed = false"
            try:
                results = self.service.files().list(
                    q=assignment_query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True
                ).execute()
                items = results.get('files', [])
                if items:
                    os.makedirs(local_data_path, exist_ok=True)
                    self.download_file(items[0]['id'], assignment_file)
                    logging.info("Successfully downloaded assignment.json from Google Drive.")
                else:
                    logging.error("assignment.json not found on Google Drive. Cannot sync preprocessor tasks.")
                    return
            except HttpError as error:
                logging.error(f"Error looking up assignment.json on Google Drive: {error}")
                return

        with open(assignment_file, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
            
        if preprocessor_name not in assignments:
            logging.error(f"Preprocessor '{preprocessor_name}' not found in assignment file.")
            return
            
        preprocessor_tasks = assignments[preprocessor_name]
        logging.info(f"Downloading all tasks for preprocessor: {preprocessor_name}")

        for book, chapters in preprocessor_tasks.items():
            if book == "total_duration_hours":
                continue
                
            if chapters == "all":
                self.download_book(local_data_path, book, parent_id)
            else:
                book_id = self.get_folder_id(book, parent_id)
                if not book_id:
                    logging.warning(f"Book folder '{book}' not found on Google Drive.")
                    continue
                for chapter in chapters:
                    self.download_chapter(local_data_path, book, chapter, book_id)
