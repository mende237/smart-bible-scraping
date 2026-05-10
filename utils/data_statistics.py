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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract statistics from scraped Bible audio and text files.')
    parser.add_argument(
        '--data_folder',
        type=str,
        default='../scraping/data/ewondo',
        help='Path to the data folder containing the scraped files.'
    )
    args = parser.parse_args()
    
    get_statictics(args.data_folder)