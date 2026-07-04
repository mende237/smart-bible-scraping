import os
import re
import json
import sys
import argparse
import logging

# Add project root to sys.path to allow importing utils
project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.cli_args import create_base_parser, add_granularity_arguments
from utils.logging_config import setup_logging

setup_logging()
 
letter_mapping = {
    "e": "e",
    "ë": "ə",
    "è": "ɛ",
    "ṅ": "ŋ",
    "o": "o",
    "ò": "ɔ",
}

def convert_verse_text_to_aglc(data_path, book, chapter, verse):
    """
    Convert the verse text to AGLC format.

    Args:
        data_path (str): The path to the data directory.
        book (str): The book name.
        chapter (str): The chapter code.
        verse (str): The verse code.
    """
    
    if os.path.exists(os.path.join(data_path, book, chapter, verse)):
        for file in os.listdir(os.path.join(data_path, book, chapter, verse)):
            match = re.match(r'^V_\d+_UTT_(\d+)\.txt$', file)
            if match:
                text_file_path = os.path.join(data_path, book, chapter, verse, file)
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Convert the text using the letter mapping
                converted_text = ''.join(letter_mapping.get(char, char) for char in text)
                
                converted_file_name = file.replace('.txt', '_AGLC.txt')
                converted_file_path = os.path.join(data_path, book, chapter, verse, converted_file_name)
                with open(converted_file_path, 'w', encoding='utf-8') as f:
                    f.write(converted_text)   
                    
def convert_chapter_text_to_aglc(data_path, book, chapter):
    """
    Convert all verse texts in a chapter to AGLC format.

    Args:
        data_path (str): The path to the data directory.
        book (str): The book name.
        chapter (str): The chapter code.
    """
    
    chapter_path = os.path.join(data_path, book, chapter)
    if os.path.exists(chapter_path):
        for verse in os.listdir(chapter_path):
            verse_path = os.path.join(chapter_path, verse)
            if os.path.isdir(verse_path):
                convert_verse_text_to_aglc(data_path, book, chapter, verse)
                
                
def convert_chapters_text_to_aglc(data_path, book, chapters):
    """
    Convert all verse texts in multiple chapters to AGLC format.

    Args:
        data_path (str): The path to the data directory.
        book (str): The book name.
        chapters (list): A list of chapter codes.
    """
    for chapter in chapters:
        convert_chapter_text_to_aglc(data_path, book, chapter)
        
        
    
def convert_book_text_to_aglc(data_path, book):
    """
    Convert all verse texts in a book to AGLC format.

    Args:
        data_path (str): The path to the data directory.
        book (str): The book name.
    """
    
    book_path = os.path.join(data_path, book)
    if os.path.exists(book_path):
        for chapter in os.listdir(book_path):
            chapter_path = os.path.join(book_path, chapter)
            if os.path.isdir(chapter_path):
                convert_chapter_text_to_aglc(data_path, book, chapter)
                
                
def convert_books_text_to_aglc(data_path, books):
    """
    Convert all verse texts in multiple books to AGLC format.

    Args:
        data_path (str): The path to the data directory.
        books (list): A list of book names.
    """
    for book in books:
        convert_book_text_to_aglc(data_path, book)
        


def convert_preprocessor_text_to_aglc(data_path, preprocessor_name):
    """
    Convert all verse texts in a preprocessor to AGLC format.

    Args:
        data_path (str): The path to the data directory.
        preprocessor_name (str): The name of the preprocessor.
    """
    
    assignment_file = os.path.join(data_path, "assignment.json")
    
    if not os.path.exists(assignment_file):
        raise FileNotFoundError(f"Assignment file not found: {assignment_file}")
        
    with open(assignment_file, 'r', encoding='utf-8') as f:
        assignments = json.load(f)
        
    if preprocessor_name not in assignments:
        raise ValueError(f"Preprocessor '{preprocessor_name}' not found in assignment file.")
        
    preprocessor_tasks = assignments[preprocessor_name]
    
    for book, chapters in preprocessor_tasks.items():
        if book == "total_duration_hours":
            continue
            
        if chapters == "all":
            convert_book_text_to_aglc(data_path, book)
        else:
            for chapter in chapters:
                convert_chapter_text_to_aglc(data_path, book, chapter)
                 

if __name__ == '__main__':
    parser = create_base_parser('Convert verse transcriptions to AGLC format.')
    add_granularity_arguments(parser, include_verse=True, include_preprocessor=True, include_books=True, include_chapters=True)
    args = parser.parse_args()

    try:
        if args.preprocessor:
            logging.info(f"Converting texts for preprocessor: {args.preprocessor}")
            convert_preprocessor_text_to_aglc(args.data_folder, args.preprocessor)
        elif args.books:
            logging.info(f"Converting texts for books: {', '.join(args.books)}")
            convert_books_text_to_aglc(args.data_folder, args.books)
        elif args.verse:
            if not args.book or not args.chapter:
                parser.error("--book and --chapter are required when --verse is specified.")
            logging.info(f"Converting text for verse: {args.verse} in {args.book}/{args.chapter}")
            convert_verse_text_to_aglc(args.data_folder, args.book, args.chapter, args.verse)
        elif args.chapters:
            if not args.book:
                parser.error("--book is required when --chapters is specified.")
            logging.info(f"Converting texts for chapters: {', '.join(args.chapters)} in {args.book}")
            convert_chapters_text_to_aglc(args.data_folder, args.book, args.chapters)
        elif args.chapter:
            if not args.book:
                parser.error("--book is required when --chapter is specified.")
            logging.info(f"Converting text for chapter: {args.chapter} in {args.book}")
            convert_chapter_text_to_aglc(args.data_folder, args.book, args.chapter)
        elif args.book:
            logging.info(f"Converting texts for book: {args.book}")
            convert_book_text_to_aglc(args.data_folder, args.book)
        else:
            parser.error("You must specify a scope: --preprocessor, --book(s), or --chapter(s).")
        logging.info("Conversion complete.")
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
                    
