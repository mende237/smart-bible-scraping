import os
import argparse
import logging
import sys
import json

# Add the current directory to sys.path to allow relative-like imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from validator import verify_verse, verify_chapter, verify_book, verify_preprocessor
except ImportError:
    from .validator import verify_verse, verify_chapter, verify_book, verify_preprocessor

# Configure logging to output to a file in the data-verification folder
log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'verification_errors.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

LANGUAGE = "ewondo"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Verify verse transcriptions against the expected text.')
    parser.add_argument(
        '--data_folder',
        type=str,
        default='../scraping/data/ewondo',
        help='Path to the data folder containing the scraped files.'
    )
    parser.add_argument(
        '--book',
        type=str,
        default=None,
        help='Specific book to process (e.g., LUK).'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        default=None,
        help='Specific chapter to process (e.g., LUK_1).'
    )
    parser.add_argument(
        '--verse',
        type=str,
        default=None,
        help='Specific verse to process (e.g., V_1).'
    )
    parser.add_argument(
        '--preprocessor',
        type=str,
        default=None,
        help='Specific preprocessor to verify (e.g., pre_processor_1). Requires assignment.json in data folder.'
    )
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
        elif args.verse:
            if not args.book or not args.chapter:
                parser.error("--book and --chapter are required when --verse is specified.")
            success = verify_verse(args.data_folder, args.book, args.chapter, args.verse, LANGUAGE)
            if not success:
                results["failures"] = {args.book: {args.chapter: [args.verse]}}
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
            parser.error("You must specify either --preprocessor, or --book.")
            
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
