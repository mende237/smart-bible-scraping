import os
import re
import argparse
import sys

# Add project root to sys.path to allow importing utils
project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.cli_args import create_base_parser, add_granularity_arguments

def pre_processing_verses_chapter(data_folder, book, chapter):
    chapter_path = os.path.join(data_folder, book, chapter)
    
    if not os.path.isdir(chapter_path):
        raise ValueError(f"Chapter folder not found: {chapter_path}")
    
    for file in os.listdir(chapter_path):
        if file.endswith('.txt'):
            file_path = os.path.join(chapter_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                verses = f.readlines()
            
            pre_processed_verses = []
            for verse in verses:
                verse = verse.strip()
                if not verse:
                    continue
                
                if re.match(r'^\[.*?\]', verse) or not pre_processed_verses:
                    pre_processed_verses.append(verse)
                else:
                    pre_processed_verses[-1] += ' ' + verse
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(pre_processed_verses))
                
                
                
                

# This function reads the verses from the Ewondo text files, removes extra whitespace, and saves the cleaned verses back to the same file.
def pre_processing_verses(data_folder):
    for book in os.listdir(data_folder):
        if os.path.isdir(os.path.join(data_folder, book)):
            for chapter in os.listdir(os.path.join(data_folder,  book)):
                if os.path.isdir(os.path.join(data_folder, book, chapter)):
                    pre_processing_verses_chapter(data_folder, book, chapter)



if __name__ == '__main__':
    parser = create_base_parser('Pre-process scraped Bible text files.')
    add_granularity_arguments(parser)
    args = parser.parse_args()
    
    if args.book and args.chapter:
        pre_processing_verses_chapter(args.data_folder, args.book, args.chapter)
    else:
        pre_processing_verses(args.data_folder)
                        
                        
