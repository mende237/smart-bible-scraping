import os
import re
import logging
import json
try:
    from validator_utils import remove_punctuation, download_text_chapter_if_missing, get_verse_text
except ImportError:
    from .validator_utils import remove_punctuation, download_text_chapter_if_missing, get_verse_text

def verify_verse(data_path, book, chapter, verse, language="ewondo"):
    try:
        actual_text = get_verse_text(data_path, book, chapter, verse)
        chapter_folder = os.path.join(data_path, book, chapter)
        
        if not os.path.isdir(chapter_folder):
            raise ValueError(f"Chapter folder not found: {chapter_folder}")
        
        chapter_text_file_path = os.path.join(chapter_folder, f"{chapter}_{language}_original.txt")
        if not os.path.exists(chapter_text_file_path):
            chapter_text_file_path = download_text_chapter_if_missing(data_path, book, chapter, language)
            
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
            
        logging.debug(f"Actual text: '{actual_text}'")
        logging.debug(f"Expected text: '{expected_text}'")
        
        actual_clean = remove_punctuation(actual_text) if actual_text else ""
        expected_clean = remove_punctuation(expected_text)
        
        if actual_clean != expected_clean:
            raise AssertionError(f"Expected '{expected_clean}', but got '{actual_clean}'")
        
        print(f"Verse {verse} verification passed!")
        return True
    except Exception as e:
        print(f"Verse {verse} verification failed: {e}")
        logging.error(f"{book} {chapter} {verse} - {e}")
        return False

def verify_chapter(data_path, book, chapter, language="ewondo"):
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
        if not verify_verse(data_path, book, chapter, verse, language):
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


def verify_book(data_path, book, language="ewondo"):
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
        failed_verses = verify_chapter(data_path, book, chapter, language)
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


def verify_preprocessor(data_path, preprocessor_name, language="ewondo"):
    logging.info(f"Starting verification for preprocessor: {preprocessor_name}")
    assignment_file = os.path.join(data_path, "assignment.json")
    
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
            failed_chapters = verify_book(data_path, book, language)
            if failed_chapters:
                failed_tasks[book] = failed_chapters
        else:
            for chapter in chapters:
                failed_verses = verify_chapter(data_path, book, chapter, language)
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
