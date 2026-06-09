import os
import re
import subprocess

language = "ewondo"


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
                "--language", language
            ], check=True)
            print(f"Successfully downloaded text for {chapter}.")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading text for {chapter}: {e}")
            
    return text_file_path


def get_verse_text(data_path, book, chapter, verse):
    verse_folder = os.path.join(data_path, book, chapter, verse)
    chapter_folder = os.path.join(data_path, book, chapter)
    
    
    if not os.path.isdir(chapter_folder):
        raise ValueError(f"Chapter folder not found: {chapter_folder}")
    
    
    if not os.path.exists(os.path.join(chapter_folder, f"{chapter}_{language}_original.txt")):
        chapter_text_file_path = download_text_chapter_if_missing(data_path, book, chapter)
    
    
    if os.path.isdir(verse_folder):
        utt_files = {}
        for file in os.listdir(verse_folder):
            match = re.match(r'^V_\d+_UTT_(\d+)\.txt$', file)
            if match:
                wav_file = file.replace('.txt', '.wav')
                if os.path.exists(os.path.join(verse_folder, wav_file)):
                    utt_files[int(match.group(1))] = file
                else:
                    print(f"Warning: Missing corresponding .wav file for {file}")
        
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
    

def verify_verse(data_path, book, chapter, verse, expected_text):
    # This is a placeholder function. In a real implementation, this would
    # retrieve the verse text from a data source and compare it to the expected text.
    actual_text = get_verse_text(data_path, book, chapter, verse)
    assert actual_text == expected_text, f"Expected '{expected_text}', but got '{actual_text}'"
    
    
if __name__ == "__main__":
    data_path = "../scraping/data/ewondo"
    book = "LUK"
    chapter = "LUK_1"
    verse = "V_1"
    expected_text = "In the beginning God created the heavens and the earth."
    
    verify_verse(data_path, book, chapter, verse, expected_text)