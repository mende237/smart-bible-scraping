import os
import argparse
import logging
import sys
import json

# Add the project root to sys.path to allow importing utils
project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Add the current directory to sys.path to allow relative-like imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cli_args import create_base_parser, add_granularity_arguments

from utils.logging_config import setup_logging

try:
    from validator import verify_verse, verify_chapter, verify_chapters, verify_book, verify_books, verify_preprocessor
except ImportError:
    from .validator import verify_verse, verify_chapter, verify_chapters, verify_book, verify_books, verify_preprocessor

# Configure logging
log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'verification_errors.log')
setup_logging(log_file=log_file_path)

LANGUAGE = "ewondo"

if __name__ == "__main__":
    parser = create_base_parser('Verify verse transcriptions against the expected text.')
    add_granularity_arguments(parser, include_verse=True, include_preprocessor=True, include_books=True, include_chapters=True)
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output failures in JSON format to stdout.'
    )
    args = parser.parse_args()
    
    results = {"failed": False, "failures": {}}
    
    try:
        if args.preprocessor:
            failures = verify_preprocessor(args.data_folder, args.preprocessor, LANGUAGE)
            results["failures"] = failures
        elif args.books:
            failures = verify_books(args.data_folder, args.books, LANGUAGE)
            if failures:
                results["failures"] = failures
        elif args.verse:
            if not args.book or not args.chapter:
                parser.error("--book and --chapter are required when --verse is specified.")
            success = verify_verse(args.data_folder, args.book, args.chapter, args.verse, LANGUAGE)
            if not success:
                results["failures"] = {args.book: {args.chapter: [args.verse]}}
        elif args.chapters:
            if not args.book:
                parser.error("--book is required when --chapters is specified.")
            failures = verify_chapters(args.data_folder, args.book, args.chapters, LANGUAGE)
            if failures:
                results["failures"] = {args.book: failures}
        elif args.chapter:
            if not args.book:
                parser.error("--book is required when --chapter is specified.")
            failures = verify_chapter(args.data_folder, args.book, args.chapter, LANGUAGE)
            if failures:
                results["failures"] = {args.book: {args.chapter: failures}}
        elif args.book:
            failures = verify_book(args.data_folder, args.book, LANGUAGE)
            if failures:
                results["failures"] = {args.book: failures}
        else:
            parser.error("You must specify either --preprocessor, --book, --books, or --chapters.")
            
        if results["failures"]:
            results["failed"] = True
            
        if args.json:
            print("---JSON_START---")
            print(json.dumps(results))
            print("---JSON_END---")
            
        if results["failed"] and not args.json:
            sys.exit(1)
            
    except Exception as e:
        if args.json:
            print("---JSON_START---")
            print(json.dumps({"failed": True, "error": str(e)}))
            print("---JSON_END---")
        else:
            print(f"Verification error: {e}")
        sys.exit(1)
