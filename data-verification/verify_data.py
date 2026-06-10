import os
import re
import subprocess
import logging
import argparse
import json

# Configure logging to output to a file in the data-verification folder
log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'verification_errors.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

language = "ewondo"


def remove_ponctuation(text):
    ponctuation_pattern = r'[^\w\s]'
    cleaned_text = re.sub(ponctuation_pattern, '', text)
    return cleaned_text.strip().lower()


def download_text_chapter_if_missing(data_path, book, chapter):
    chapter_folder = os.path.join(data_path, book, chapter)
    
    if not os.path.isdir(chapter_folder):
        raise ValueError(f"Chapter folder not found: {chapter_folder}")
    
    text_file_path = os.path.join(chapter_folder, f"{chapter}_{language}_original.txt")
    
    if not os.path.exists(text_file_path):
        print(f"Text file missing for {book} {chapter}. Downloading...")
        
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraping', 'src', 'scrapping.js'))
        chapter_num = chapter.split('_')[-1]
        
        try:
            subprocess.run([
                "node", script_path,
                "--book", book,
                "--chapter", chapter_num,
                "--text-only",
                "--single-chapter",
                "--suffix", "original",
                "--language", language,
                "--download-folder", data_path
            ], check=True)
            print(f"Successfully downloaded text for {chapter}.")
            
            pre_process_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data-pre-processing', 'pre_process_verses.py'))
            print(f"Pre-processing downloaded text for {chapter}...")
            subprocess.run([
                "python", pre_process_script_path,
                "--data_folder", data_path,
                "--book", book,
                "--chapter", chapter
            ], check=True)
            print(f"Successfully pre-processed text for {chapter}.")
        except subprocess.CalledProcessError as e:
            error_msg = f"Error downloading or pre-processing text for {chapter}: {e}"
            print(error_msg)
            logging.error(error_msg)
            
    return text_file_path


def get_verse_text(data_path, book, chapter, verse):
    verse_folder = os.path.join(data_path, book, chapter, verse)
    
    if os.path.isdir(verse_folder):
        utt_files = {}
        for file in os.listdir(verse_folder):
            match = re.match(r'^V_\d+_UTT_(\d+)\.txt$', file)
            if match:
                wav_file = file.replace('.txt', '.wav')
                if os.path.exists(os.path.join(verse_folder, wav_file)):
                    utt_files[int(match.group(1))] = file
                else:
                    warning_msg = f"Warning: Missing corresponding .wav file for {file} in {verse_folder}"
                    print(warning_msg)
                    logging.warning(warning_msg)
        
        if utt_files:
            utt_numbers = sorted(utt_files.keys())
            expected_numbers = list(range(1, max(utt_numbers) + 1))
            
            if utt_numbers != expected_numbers:
                raise ValueError(f"Missing or non-sequential UTT numbers in {verse_folder}. Found: {utt_numbers}")
            
            texts = []
            for num in utt_numbers:
                with open(os.path.join(verse_folder, utt_files[num]), 'r') as f:
                    texts.append(f.read().strip())
                    
            
            return " ".join(texts)
    

def verify_verse(data_path, book, chapter, verse):
    actual_text = get_verse_text(data_path, book, chapter, verse)
    chapter_folder = os.path.join(data_path, book, chapter)
    

    if not os.path.isdir(chapter_folder):
        raise ValueError(f"Chapter folder not found: {chapter_folder}")
    
    chapter_text_file_path = os.path.join(chapter_folder, f"{chapter}_{language}_original.txt")
    if not os.path.exists(chapter_text_file_path):
        chapter_text_file_path = download_text_chapter_if_missing(data_path, book, chapter)
        
    verse_num = verse.split('_')[-1]
    expected_text = None
    
    with open(chapter_text_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.match(rf'^\[{verse_num}\]\s*(.*)', line.strip())
            if match:
                expected_text = match.group(1)
                break
                
    if expected_text is None:
        raise ValueError(f"Verse {verse_num} not found in {chapter_text_file_path}")
        
    print(f"Actual text: '{actual_text}'")
    print(f"Expected text: '{expected_text}'")
    
    actual_clean = remove_ponctuation(actual_text) if actual_text else ""
    expected_clean = remove_ponctuation(expected_text)
    
    assert actual_clean == expected_clean, f"Expected '{expected_clean}', but got '{actual_clean}'"
    print(f"Verse {verse} verification passed!")
    

def verify_chapter(data_path, book, chapter):
    logging.info(f"Starting verification for {book} - {chapter}")
    chapter_folder = os.path.join(data_path, book, chapter)
    
    if not os.path.isdir(chapter_folder):
        raise ValueError(f"Chapter folder not found: {chapter_folder}")
        
    verse_folders = []
    for item in os.listdir(chapter_folder):
        if os.path.isdir(os.path.join(chapter_folder, item)) and re.match(r'^V_\d+$', item):
            verse_folders.append(item)
            
    verse_folders.sort(key=lambda x: int(x.split('_')[1]))
    
    failed_verses = []
    for verse in verse_folders:
        try:
            verify_verse(data_path, book, chapter, verse)
        except Exception as e:
            error_msg = f"Verification failed for {verse}: {e}"
            print(error_msg)
            logging.error(f"{book} {chapter} {verse} - {e}")
            failed_verses.append(verse)
            
    if failed_verses:
        summary_msg = f"\nChapter {chapter} verification completed with errors in verses: {', '.join(failed_verses)}"
        print(summary_msg)
        logging.warning(summary_msg.strip())
    else:
        success_msg = f"\nAll verses in chapter {chapter} verified successfully!"
        print(success_msg)
        logging.info(success_msg.strip())
        
    return failed_verses


def verify_book(data_path, book):
    logging.info(f"Starting verification for book: {book}")
    book_folder = os.path.join(data_path, book)
    
    if not os.path.isdir(book_folder):
        raise ValueError(f"Book folder not found: {book_folder}")
        
    chapter_folders = []
    for item in os.listdir(book_folder):
        if os.path.isdir(os.path.join(book_folder, item)) and item.startswith(f"{book}_"):
            chapter_folders.append(item)
            
    # Sort chapters numerically based on the chapter number
    chapter_folders.sort(key=lambda x: int(x.split('_')[1]) if len(x.split('_')) > 1 and x.split('_')[1].isdigit() else 0)
    
    failed_chapters = {}
    for chapter in chapter_folders:
        failed_verses = verify_chapter(data_path, book, chapter)
        if failed_verses:
            failed_chapters[chapter] = failed_verses
            
    if failed_chapters:
        summary_msg = f"\nBook {book} verification completed with errors in chapters: {', '.join(failed_chapters.keys())}"
        print(summary_msg)
        logging.warning(summary_msg.strip())
    else:
        success_msg = f"\nAll chapters in book {book} verified successfully!"
        print(success_msg)
        logging.info(success_msg.strip())
        
    return failed_chapters


def verify_preprocessor(data_path, preprocessor_name):
    logging.info(f"Starting verification for preprocessor: {preprocessor_name}")
    assignment_file = os.path.join(data_path, "assignement.json")
    
    if not os.path.exists(assignment_file):
        raise FileNotFoundError(f"Assignment file not found: {assignment_file}")
        
    with open(assignment_file, 'r', encoding='utf-8') as f:
        assignments = json.load(f)
        
    if preprocessor_name not in assignments:
        raise ValueError(f"Preprocessor '{preprocessor_name}' not found in assignment file.")
        
    preprocessor_tasks = assignments[preprocessor_name]
    
    failed_tasks = {}
    for book, chapters in preprocessor_tasks.items():
        if book == "total_duration_hours":
            continue
            
        if chapters == "all":
            failed_chapters = verify_book(data_path, book)
            if failed_chapters:
                failed_tasks[book] = failed_chapters
        else:
            for chapter in chapters:
                failed_verses = verify_chapter(data_path, book, chapter)
                if failed_verses:
                    if book not in failed_tasks:
                        failed_tasks[book] = {}
                    failed_tasks[book][chapter] = failed_verses
                    
    if failed_tasks:
        summary_msg = f"\nPreprocessor {preprocessor_name} verification completed with errors."
        print(summary_msg)
        logging.warning(summary_msg.strip())
    else:
        success_msg = f"\nAll assigned tasks for preprocessor {preprocessor_name} verified successfully!"
        print(success_msg)
        logging.info(success_msg.strip())
        
    return failed_tasks

    
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
        help='Specific preprocessor to verify (e.g., pre_processor_1). Requires assignement.json in data folder.'
    )
    args = parser.parse_args()
    
    if args.preprocessor:
        verify_preprocessor(args.data_folder, args.preprocessor)
    elif args.verse:
        if not args.book or not args.chapter:
            parser.error("--book and --chapter are required when --verse is specified.")
        verify_verse(args.data_folder, args.book, args.chapter, args.verse)
    elif args.chapter:
        if not args.book:
            parser.error("--book is required when --chapter is specified.")
        verify_chapter(args.data_folder, args.book, args.chapter)
    elif args.book:
        verify_book(args.data_folder, args.book)
    else:
        parser.error("You must specify either --preprocessor, or --book.")