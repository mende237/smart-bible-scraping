import os
import argparse
import logging
import sys

# Add the project root to sys.path to allow importing utils
project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Add the current directory to sys.path to allow relative-like imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cli_args import create_base_parser, add_granularity_arguments

from utils.logging_config import setup_logging

try:
    from synchronizer import DataSynchronizer
    from config import PARENT_FOLDER_ID, BASE_DIR
except ImportError:
    from .synchronizer import DataSynchronizer
    from .config import PARENT_FOLDER_ID, BASE_DIR

setup_logging()

def handle_download(parser, args, synchronizer, data_path, lang_id):
    """Handles the downloading workflow from Google Drive to local data path."""
    if args.preprocessor:
        synchronizer.download_preprocessor(data_path, args.preprocessor, lang_id)
    elif args.verse:
        if not args.book or not args.chapter:
            parser.error("--book and --chapter are required with --verse.")
        book_id = synchronizer.get_folder_id(args.book, lang_id)
        if not book_id:
            logging.error(f"Book '{args.book}' not found on Google Drive.")
            return
        chapter_id = synchronizer.get_folder_id(args.chapter, book_id)
        if not chapter_id:
            logging.error(f"Chapter '{args.chapter}' not found on Google Drive.")
            return
        synchronizer.download_verse(data_path, args.book, args.chapter, args.verse, chapter_id)
    elif args.chapters:
        if not args.book:
            parser.error("--book is required with --chapters.")
        book_id = synchronizer.get_folder_id(args.book, lang_id)
        if not book_id:
            logging.error(f"Book '{args.book}' not found on Google Drive.")
            return
        synchronizer.download_chapters(data_path, args.book, args.chapters, book_id)
    elif args.chapter:
        if not args.book:
            parser.error("--book is required with --chapter.")
        book_id = synchronizer.get_folder_id(args.book, lang_id)
        if not book_id:
            logging.error(f"Book '{args.book}' not found on Google Drive.")
            return
        synchronizer.download_chapter(data_path, args.book, args.chapter, book_id)
    elif args.books:
        synchronizer.download_books(data_path, args.books, lang_id)
    elif args.book:
        synchronizer.download_book(data_path, args.book, lang_id)
    else:
        parser.error("Specify --book, --books, --chapter, --chapters, --verse, or --preprocessor.")

def handle_upload(parser, args, synchronizer, data_path, lang_id):
    """Handles the uploading/synchronisation workflow from local to Google Drive."""
    if args.preprocessor:
        synchronizer.sync_preprocessor(data_path, args.preprocessor, lang_id)
    elif args.verse:
        if not args.book or not args.chapter:
            parser.error("--book and --chapter are required with --verse.")
        book_id = synchronizer.get_or_create_folder(args.book, lang_id)
        chapter_id = synchronizer.get_or_create_folder(args.chapter, book_id)
        synchronizer.sync_verse(data_path, args.book, args.chapter, args.verse, chapter_id)
    elif args.chapters:
        if not args.book:
            parser.error("--book is required with --chapters.")
        book_id = synchronizer.get_or_create_folder(args.book, lang_id)
        synchronizer.sync_chapters(data_path, args.book, args.chapters, book_id)
    elif args.chapter:
        if not args.book:
            parser.error("--book is required with --chapter.")
        book_id = synchronizer.get_or_create_folder(args.book, lang_id)
        synchronizer.sync_chapter(data_path, args.book, args.chapter, book_id)
    elif args.books:
        synchronizer.sync_books(data_path, args.books, lang_id)
    elif args.book:
        synchronizer.sync_book(data_path, args.book, lang_id)
    else:
        parser.error("Specify --book, --books, --chapter, --chapters, --verse, or --preprocessor.")

def main():
    parser = create_base_parser('Synchronizes local data with Google Drive.')
    add_granularity_arguments(parser, include_verse=True, include_preprocessor=True, include_books=True, include_chapters=True)
    parser.add_argument('--headless', action='store_true', help='Console mode auth.')
    parser.add_argument('--no-verify', action='store_true', help='Skip verification.')
    parser.add_argument('--download', action='store_true', help='Download from Google Drive instead of uploading.')
    
    args = parser.parse_args()
    
    if not PARENT_FOLDER_ID:
        logging.error("DRIVE_FOLDER_ID not set in .env")
        return
 
    data_path = os.path.normpath(os.path.join(BASE_DIR, args.data_folder)) if not os.path.isabs(args.data_folder) else args.data_folder
 
    synchronizer = DataSynchronizer(headless=args.headless)
 
    # 1. Verification Gate
    if not args.no_verify and not args.download:
        if not args.book and not args.preprocessor and not args.books:
            parser.error("At least --book, --books, or --preprocessor is required unless --no-verify is used.")
        if not synchronizer.run_verification(
            data_path=data_path,
            book=args.book,
            chapter=args.chapter,
            verse=args.verse,
            preprocessor=args.preprocessor,
            books=args.books,
            chapters=args.chapters
        ):
            return

    # 2. Sync Execution
    if args.download:
        lang_id = synchronizer.get_folder_id(os.path.basename(data_path), PARENT_FOLDER_ID)
        if not lang_id:
            logging.error(f"Language folder '{os.path.basename(data_path)}' not found on Google Drive.")
            return
        handle_download(parser, args, synchronizer, data_path, lang_id)
    else:
        lang_id = synchronizer.get_or_create_folder(os.path.basename(data_path), PARENT_FOLDER_ID)
        if not lang_id: return
        handle_upload(parser, args, synchronizer, data_path, lang_id)

if __name__ == '__main__':
    main()
