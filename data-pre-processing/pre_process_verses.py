import os
import re
import argparse

# This function reads the verses from the Ewondo text files, removes extra whitespace, and saves the cleaned verses back to the same file.
def pre_processing_verses(data_folder):
    for book in os.listdir(data_folder):
        for chapter in os.listdir(os.path.join(data_folder,  book)):
            chapter_path = os.path.join(data_folder, book, chapter)
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pre-process scraped Bible text files.')
    parser.add_argument(
        '--data_folder',
        type=str,
        default='../scraping/data/ewondo',
        help='Path to the data folder containing the scraped files.'
    )
    args = parser.parse_args()
    
    pre_processing_verses(args.data_folder)
                        
                        
