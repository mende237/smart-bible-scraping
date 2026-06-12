import os
import re
import subprocess
import logging

def remove_punctuation(text):
    punctuation_pattern = r'[^\w\s]'
    cleaned_text = re.sub(punctuation_pattern, '', text)
    return cleaned_text.strip().lower()


def download_text_chapter_if_missing(data_path, book, chapter, language="ewondo"):
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
    return None
