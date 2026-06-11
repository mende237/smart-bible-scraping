import os
import mimetypes
import subprocess
import sys
import logging
import json
from typing import Optional
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
try:
    from auth import get_drive_service
except ImportError:
    from .auth import get_drive_service

class DataSynchronizer:
    def __init__(self, headless: bool = False):
        self.service = get_drive_service(headless)

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

    def upload_file(self, local_path: str, parent_id: str):
        """Uploads or updates a file on Google Drive."""
        file_name = os.path.basename(local_path)
        query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
        
        try:
            results = self.service.files().list(
                q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            items = results.get('files', [])
            
            mime_type, _ = mimetypes.guess_type(local_path)
            media = MediaFileUpload(local_path, mimetype=mime_type or 'application/octet-stream')
            
            if items:
                file_id = items[0]['id']
                self.service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
                logging.info(f"File updated: {file_name}")
            else:
                file_metadata = {'name': file_name, 'parents': [parent_id]}
                self.service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
                logging.info(f"File imported: {file_name}")
        except HttpError as error:
            if error.resp.status == 403 and "storageQuotaExceeded" in str(error):
                logging.error("Storage quota exceeded. Consider switching to OAuth2.")
            else:
                logging.error(f"Error importing '{file_name}': {error}")

    def run_verification(self, data_path: str, book: str = None, chapter: str = None, verse: str = None, preprocessor: str = None) -> bool:
        """Runs the external verification script."""
        logging.info("="*50)
        logging.info("STARTING DATA VERIFICATION")
        logging.info("="*50)
        
        script_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data-verification', 'verify_data.py'))
        cmd = [sys.executable, script_path, '--data_folder', data_path]
        if preprocessor: cmd.extend(['--preprocessor', preprocessor])
        elif verse: cmd.extend(['--book', book, '--chapter', chapter, '--verse', verse])
        elif chapter: cmd.extend(['--book', book, '--chapter', chapter])
        elif book: cmd.extend(['--book', book])
        
        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                logging.error("VERIFICATION FAILED. ABORTING SYNC.")
                return False
            logging.info("Data verification successful.\n")
            return True
        except Exception as e:
            logging.error(f"Verification execution error: {e}")
            return False

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
