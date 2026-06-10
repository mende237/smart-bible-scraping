import os
import re
import argparse

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
    parser = argparse.ArgumentParser(description='Pre-process scraped Bible text files.')
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
        help='Specific book to process (e.g., MAT).'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        default=None,
        help='Specific chapter to process (e.g., MAT_1).'
    )
    args = parser.parse_args()
    
    if args.book and args.chapter:
        pre_processing_verses_chapter(args.data_folder, args.book, args.chapter)
    else:
        pre_processing_verses(args.data_folder)
                        
                        
