import os
import sys
import argparse
import re

def generate_verses_folder(data_path):
    for book in os.listdir(data_path):
        book_path = os.path.join(data_path, book)
        if os.path.isdir(book_path):
            for chapter in os.listdir(book_path):
                chapter_path = os.path.join(book_path, chapter)
                if os.path.isdir(chapter_path):
                    found_txt_file = False
                    for file in os.listdir(chapter_path):
                        if found_txt_file:
                            break
                        if file.endswith('.txt'):
                            found_txt_file = True
                            verse_path = os.path.join(chapter_path, file)
                            with open(verse_path, 'r') as f:
                                verse_text = f.read()
                                verse_numbers = re.findall(r'\[(\d+)\]', verse_text)
                                if verse_numbers:
                                    for verse_number in verse_numbers:
                                        verse_folder = os.path.join(chapter_path, f"V_{verse_number}")
                                        os.makedirs(verse_folder, exist_ok=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate verses folder from the pre-processed data.')
    parser.add_argument(
        '--data_folder',
        type=str,
        default='../scraping/data/ewondo',
        help='Path to the data folder containing the scraped files.'
    )
    args = parser.parse_args()
    
    generate_verses_folder(args.data_folder)