import os
import argparse
import statistics
import json
from pydub import AudioSegment


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
                            print(f"Warning: Skipping empty file: {mp3_path}")
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
                        print(f"Warning: Failed to process {mp3_path}: {str(e)}")
                    
                    
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



def get_segmented_chapter_statistics(data_folder, book, chapter, dump = True):
    chapter_path = os.path.join(data_folder, book, chapter)
    stats = {
        "total_duration_seconds": 0,
        "durations": []
    }
                    
    if not os.path.exists(chapter_path):
        print(f"Error: Chapter path '{chapter_path}' does not exist.")
        return None, None
    
    for verse in os.listdir(chapter_path):
        verse_path = os.path.join(chapter_path, verse)
        if os.path.isdir(verse_path):
            for utterance in os.listdir(verse_path):
                if utterance.endswith('.wav'):
                    wav_path = os.path.join(verse_path, utterance)
                    # Skip empty files
                    if os.path.getsize(wav_path) == 0:
                        print(f"Warning: Skipping empty file: {wav_path}")
                        continue
                    duration = AudioSegment.from_wav(wav_path).duration_seconds
                    stats["total_duration_seconds"] = stats.get("total_duration_seconds", 0) + duration
                    stats["durations"].append(duration)

    durations = stats["durations"]
    
    stats["total_duration_minutes"] = stats["total_duration_seconds"] / 60
    if len(durations) > 0:
        stats["utterance_mean_duration_seconds"] = statistics.mean(durations)
        stats["utterance_median_duration_seconds"] = statistics.median(durations)
        stats["utterance_max_duration_seconds"] = max(durations)
        stats["utterance_min_duration_seconds"] = min(durations)
    else:
        stats["utterance_mean_duration_seconds"] = 0
        stats["utterance_median_duration_seconds"] = 0
        stats["utterance_max_duration_seconds"] = 0
        stats["utterance_min_duration_seconds"] = 0
    
    del stats["durations"]
    del stats["total_duration_seconds"]
    
    if dump:
        with open(f'{data_folder}/{chapter}_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)
    
    return stats, durations


def get_segmented_book_statistics(data_folder, book, dump = True):
    book_path = os.path.join(data_folder, book)
    stats = {
        "total_duration_seconds": 0,
        "durations": []
    }
                    
    if not os.path.exists(book_path):
        print(f"Error: Book path '{book_path}' does not exist.")
        return None, None
    
    for chapter in os.listdir(book_path):        
        chapter_statistics, chapter_durations = get_segmented_chapter_statistics(data_folder, book, chapter, dump=False)
        if chapter_statistics is not None:
            stats[chapter] = chapter_statistics
            
        if chapter_durations is not None:
            stats["total_duration_seconds"] += sum(chapter_durations)
            stats["durations"].extend(chapter_durations)

    
    stats["total_duration_hours"] = stats["total_duration_seconds"] / 3600
    stats["utterance_mean_duration_seconds"] = statistics.mean(stats["durations"])
    stats["utterance_median_duration_seconds"] = statistics.median(stats["durations"])
    stats["utterance_max_duration_seconds"] = max(stats["durations"]) 
    stats["utterance_min_duration_seconds"] = min(stats["durations"]) 
    
    durations = stats["durations"]
    
    del stats["durations"]
    del stats["total_duration_seconds"]
    
    if dump:
        with open(f'{data_folder}/{book}_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)
    
    return stats, durations


def get_segmented_books_statistics(data_folder, books, dump = True):
    stats = {
        "total_duration_seconds": 0,
        "durations": []
    }
    
    for book in books:
        book_path = os.path.join(data_folder, book)
        if not os.path.exists(book_path):
            print(f"Error: Book path '{book_path}' does not exist.")
            continue
        
        book_statistics, book_durations = get_segmented_book_statistics(data_folder, book, dump=False)
        if book_statistics is not None:
            stats[book] = book_statistics
        
        if book_durations is not None:
            stats["total_duration_seconds"] += sum(book_durations)
            stats["durations"].extend(book_durations)
        
        
    stats["total_duration_hours"] = stats["total_duration_seconds"] / 3600
    stats["utterance_mean_duration_seconds"] = statistics.mean(stats["durations"])
    stats["utterance_median_duration_seconds"] = statistics.median(stats["durations"])
    stats["utterance_max_duration_seconds"] = max(stats["durations"])
    stats["utterance_min_duration_seconds"] = min(stats["durations"])
    
    
    durations = stats["durations"]
    
    del stats["durations"]
    del stats["total_duration_seconds"]
    
    file_name = '_'.join(books) + '_statistics.json'
    if dump:
        with open(f'{args.data_folder}/{file_name}', 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=4)
                
    return stats, durations




def get_segmented_preprocessor_data_statistics(data_folder, preprocessor_name, dump = True):
    assignment_file = os.path.join(data_folder, "assignment.json")
    
    if not os.path.exists(assignment_file):
        print(f"Error: Assignment file not found: {assignment_file}")
        return None, None

    with open(assignment_file, 'r', encoding='utf-8') as f:
        assignments = json.load(f)
        
    if preprocessor_name not in assignments:
        print(f"Error: Preprocessor '{preprocessor_name}' not found in assignment file.")
        return None, None
        
    preprocessor_tasks = assignments[preprocessor_name]
    stats = {
        "total_duration_seconds": 0,
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
                stats["total_duration_seconds"] += sum(book_durations)
                stats["durations"].extend(book_durations)
        else:
            for chapter in chapters:
                chapter_statistics, chapter_durations = get_segmented_chapter_statistics(data_folder, book, chapter, dump=False)
                if chapter_statistics is not None:
                    stats[f"{book}_{chapter}"] = chapter_statistics
                
                if chapter_durations is not None:
                    stats["total_duration_seconds"] += sum(chapter_durations)
                    stats["durations"].extend(chapter_durations)

    stats["total_duration_hours"] = stats["total_duration_seconds"] / 3600
    stats["utterance_mean_duration_seconds"] = statistics.mean(stats["durations"])
    stats["utterance_median_duration_seconds"] = statistics.median(stats["durations"])
    stats["utterance_max_duration_seconds"] = max(stats["durations"])
    stats["utterance_min_duration_seconds"] = min(stats["durations"])
    
    durations = stats["durations"]
    
    del stats["durations"]
    del stats["total_duration_seconds"]
    
    file_name = f"{preprocessor_name}_statistics.json"
    if dump:
        with open(f'{data_folder}/{file_name}', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)


    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract statistics from scraped Bible audio and text files.')
    parser.add_argument(
        '--data_folder',
        type=str,
        default='../scraping/data/ewondo',
        help='Path to the data folder containing the scraped files.'
    )

    # Group for mutually exclusive book arguments
    selection_group = parser.add_mutually_exclusive_group()
    selection_group.add_argument(
        '--book',
        type=str,
        default=None,
        help='A single book to get statistics for (e.g., LUK). Can be used with --chapter.'
    )
    selection_group.add_argument(
        '--books',
        nargs='+',
        type=str,
        default=None,
        help='A list of books to get segmented statistics for (e.g., MAT LUK).'
    )
    selection_group.add_argument(
        '--preprocessor',
        type=str,
        default=None,
        help='The preprocessor to get statistics for (e.g., pre_processor_1).'
    )

    parser.add_argument(
        '--chapter',
        type=str,
        default=None,
        help='The chapter to get segmented statistics for (e.g., MAT_1). Must be used with --book.'
    )
    args = parser.parse_args()
    
    if args.chapter and not args.book:
        parser.error("--book is required when --chapter is provided.")

    if args.preprocessor:
        print(f"Getting segmented statistics for preprocessor: '{args.preprocessor}'...")
        get_segmented_preprocessor_data_statistics(args.data_folder, args.preprocessor)
    elif args.books:
        print(f"Getting segmented statistics for books: {', '.join(args.books)}...")
        stats = get_segmented_books_statistics(args.data_folder, args.books)
    elif args.book and not args.chapter:
        print(f"Getting segmented book statistics for book: '{args.book}'...")
        get_segmented_book_statistics(args.data_folder, args.book)
    elif args.book and args.chapter:
        print(f"Getting segmented chapter statistics for book: '{args.book}', chapter: '{args.chapter}'...")
        get_segmented_chapter_statistics(args.data_folder, args.book, args.chapter)
    else:
        print("Getting statistics for the entire dataset...")
        get_statictics(args.data_folder)