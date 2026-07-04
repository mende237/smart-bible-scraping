import os
import argparse
import statistics
import json
from pydub import AudioSegment
import logging

try:
    from cli_args import create_base_parser, add_granularity_arguments
    from logging_config import setup_logging
except ImportError:
    from utils.cli_args import create_base_parser, add_granularity_arguments
    from utils.logging_config import setup_logging

# Configure logging
setup_logging()
def get_statictics(data_folder):
    stats = {}
    for book in os.listdir(data_folder):
        for chapter in os.listdir(os.path.join(data_folder,  book)):
            chapter_path = os.path.join(data_folder, book, chapter)
            for file in os.listdir(chapter_path):
                if file.endswith('.txt'):
                    language = file.split('.')[0].split('_')[-1]
                    file_path = os.path.join(chapter_path, file)
                    total_verses = 0
                    with open(file_path, 'r', encoding='utf-8') as f:
                        verses = f.readlines()
                        total_verses += len(verses)
                    
                    if language not in stats:
                        stats[language] = {
                            "total_of_books": 1,
                            "total_of_chapters": 1,
                            "total_of_verses": total_verses,
                            
                        }
                    else: 
                        stats[language]["total_of_verses"] += total_verses
                        
            
                if file.endswith('.mp3'):
                    try:
                        language = file.split('.')[0].split('_')[-1]
                        mp3_path = os.path.join(chapter_path, file)
                        # Skip empty files
                        if os.path.getsize(mp3_path) == 0:
                            logging.warning(f"Skipping empty file: {mp3_path}")
                            continue
                        duration = AudioSegment.from_mp3(mp3_path).duration_seconds
                        if language not in stats:
                            stats[language] = {
                                "total_duration_seconds": duration,
                                "durations": [duration],
                            }
                        else:
                            stats[language].setdefault("total_duration_seconds", 0)
                            stats[language]["total_duration_seconds"] += duration
                            stats[language].setdefault("durations", []).append(duration)
                    except Exception as e:
                        logging.warning(f"Failed to process {mp3_path}: {str(e)}")
                    
                    
            for language in stats.keys():
                stats[language]["total_of_chapters"] += 1
        
        for language in stats.keys():
            stats[language]["total_of_books"] += 1
    
    # Calculate mean, median, max, min for durations
    for language in stats.keys():
        if "total_duration_seconds" in stats[language]:
            stats[language]["total_duration_hours"] = stats[language]["total_duration_seconds"] / 3600
            
        if "durations" in stats[language] and len(stats[language]["durations"]) > 0:
            durations = stats[language]["durations"]
            stats[language]["mean_duration_minutes"] = statistics.mean(durations) / 60
            stats[language]["median_duration_minutes"] = statistics.median(durations) / 60
            stats[language]["max_duration_minutes"] = max(durations) / 60
            stats[language]["min_duration_minutes"] = min(durations) / 60
            # Remove the durations list from output
            del stats[language]["durations"]
            del stats[language]["total_duration_seconds"]
    
    with open(f'{data_folder}/statistics.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=4)
    return stats


def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    parts = []
    if hours != 0:
        parts.append(f"{hours}h")
    if minutes != 0:
        parts.append(f"{minutes}m")

    # Always display seconds (even if 0.00)
    parts.append(f"{secs:.2f}s")

    return " ".join(parts)



def update_statistics_with_durations(stats, durations):
    if len(durations) == 0:
        stats["utterance_total_duration"] = format_duration(0)
        stats["utterance_mean_duration"] = format_duration(0)
        stats["utterance_median_duration"] = format_duration(0)
        stats["utterance_max_duration"] = format_duration(0)
        stats["utterance_min_duration"] = format_duration(0)
        return stats
    
    stats["utterance_total_duration"] = format_duration(sum(durations))
    stats["utterance_mean_duration"] = format_duration(statistics.mean(durations))
    stats["utterance_median_duration"] = format_duration(statistics.median(durations))
    stats["utterance_max_duration"] = format_duration(max(durations))
    stats["utterance_min_duration"] = format_duration(min(durations))
    return stats



def get_segmented_chapter_statistics(data_folder, book, chapter, dump = True):
    chapter_path = os.path.join(data_folder, book, chapter)
    stats = {
        "durations": []
    }
                    
    if not os.path.exists(chapter_path):
        logging.error(f"Chapter path '{chapter_path}' does not exist.")
        return None, None
    
    for verse in os.listdir(chapter_path):
        verse_path = os.path.join(chapter_path, verse)
        if os.path.isdir(verse_path):
            for utterance in os.listdir(verse_path):
                if utterance.endswith('.wav'):
                    wav_path = os.path.join(verse_path, utterance)
                    # Skip empty files
                    if os.path.getsize(wav_path) == 0:
                        logging.warning(f"Skipping empty file: {wav_path}")
                        continue
                    duration = AudioSegment.from_wav(wav_path).duration_seconds
                    stats["durations"].append(duration)

    durations = stats["durations"]
    update_statistics_with_durations(stats, durations)
    
    del stats["durations"]
    
    if dump:
        with open(f'{data_folder}/{chapter}_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)
    
    return stats, durations


def get_segmented_book_statistics(data_folder, book, dump = True):
    book_path = os.path.join(data_folder, book)
    stats = {
        "durations": []
    }
                    
    if not os.path.exists(book_path):
        logging.error(f"Book path '{book_path}' does not exist.")
        return None, None
    
    for chapter in os.listdir(book_path):        
        chapter_statistics, chapter_durations = get_segmented_chapter_statistics(data_folder, book, chapter, dump=False)
        if chapter_statistics is not None:
            stats[chapter] = chapter_statistics
            
        if chapter_durations is not None:
            stats["durations"].extend(chapter_durations)

    durations = stats["durations"]
    update_statistics_with_durations(stats, durations)
    
    del stats["durations"]
    
    if dump:
        with open(f'{data_folder}/{book}_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)
    
    return stats, durations


def get_segmented_books_statistics(data_folder, books, dump = True):
    stats = {
        "durations": []
    }
    
    for book in books:
        book_path = os.path.join(data_folder, book)
        if not os.path.exists(book_path):
            logging.error(f"Book path '{book_path}' does not exist.")
            continue
        
        book_statistics, book_durations = get_segmented_book_statistics(data_folder, book, dump=False)
        if book_statistics is not None:
            stats[book] = book_statistics
        
        if book_durations is not None:
            stats["durations"].extend(book_durations)
        
    durations = stats["durations"]
    update_statistics_with_durations(stats, durations)
    
    del stats["durations"]
        
    file_name = '_'.join(books) + '_statistics.json'
    if dump:
        with open(f'{args.data_folder}/{file_name}', 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=4)
                
    return stats, durations




def get_segmented_preprocessor_data_statistics(data_folder, preprocessor_name, dump = True):
    assignment_file = os.path.join(data_folder, "assignment.json")
    
    if not os.path.exists(assignment_file):
        logging.error(f"Assignment file not found: {assignment_file}")
        return None, None

    with open(assignment_file, 'r', encoding='utf-8') as f:
        assignments = json.load(f)
        
    if preprocessor_name not in assignments:
        logging.error(f"Preprocessor '{preprocessor_name}' not found in assignment file.")
        return None, None
        
    preprocessor_tasks = assignments[preprocessor_name]
    stats = {
        "durations": []
    }
    
    for book, chapters in preprocessor_tasks.items():
        if book == "total_duration_hours":
            continue
            
        if chapters == "all":
            book_statistics, book_durations = get_segmented_book_statistics(data_folder, book, dump=False)
            if book_statistics is not None:
                stats[book] = book_statistics
            
            if book_durations is not None:
                stats["durations"].extend(book_durations)
        else:
            for chapter in chapters:
                chapter_statistics, chapter_durations = get_segmented_chapter_statistics(data_folder, book, chapter, dump=False)
                if chapter_statistics is not None:
                    stats[f"{book}_{chapter}"] = chapter_statistics
                
                if chapter_durations is not None:
                    stats["durations"].extend(chapter_durations)

    
    durations = stats["durations"]
    update_statistics_with_durations(stats, durations)
        
    del stats["durations"]
    
    file_name = f"{preprocessor_name}_statistics.json"
    if dump:
        with open(f'{data_folder}/{file_name}', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)


    
    
if __name__ == '__main__':
    parser = create_base_parser('Extract statistics from scraped Bible audio and text files.')
    add_granularity_arguments(parser, include_preprocessor=True, include_books=True, include_chapters=True)
    args = parser.parse_args()
    
    if args.chapter and not args.book:
        parser.error("--book is required when --chapter is provided.")
        
    if args.chapters and not args.book:
        parser.error("--book is required when --chapters is provided.")

    if args.preprocessor:
        logging.info(f"Getting segmented statistics for preprocessor: '{args.preprocessor}'...")
        get_segmented_preprocessor_data_statistics(args.data_folder, args.preprocessor)
    elif args.books:
        logging.info(f"Getting segmented statistics for books: {', '.join(args.books)}...")
        stats = get_segmented_books_statistics(args.data_folder, args.books)
    elif args.book and not args.chapter and not args.chapters:
        logging.info(f"Getting segmented book statistics for book: '{args.book}'...")
        get_segmented_book_statistics(args.data_folder, args.book)
    elif args.book and args.chapter:
        logging.info(f"Getting segmented chapter statistics for book: '{args.book}', chapter: '{args.chapter}'...")
        get_segmented_chapter_statistics(args.data_folder, args.book, args.chapter)
    else:
        logging.info("Getting statistics for the entire dataset...")
        get_statictics(args.data_folder)