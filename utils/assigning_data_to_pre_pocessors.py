import os
import sys
import json
from data_statistics import get_statictics
from pydub import AudioSegment
import argparse

try:
    from cli_args import create_base_parser
except ImportError:
    from utils.cli_args import create_base_parser


def assign_data_to_pre_processors(data_path, nbr_pre_processors):
    if not os.path.exists(os.path.join(data_path, "statistics.json")):
        get_statictics(data_path)


    with open(os.path.join(data_path, "statistics.json"), "r") as f:
        statistics = json.load(f)
    
    total_duration = statistics["ewondo"]["total_duration_hours"]
    max_duration_per_processor = (total_duration / nbr_pre_processors) * 3600  # Convert hours to seconds
    
    assignment = {f"pre_processor_{i+1}": {} for i in range(nbr_pre_processors)}
    
   
    assigned_duration = 0
    i = 1
    for book in os.listdir(data_path):
        book_path = os.path.join(data_path, book)
        if not os.path.isdir(book_path):
            continue
        
        chapters = []
        for chapter in os.listdir(book_path):
            chapter_path = os.path.join(book_path, chapter)
            if not os.path.isdir(chapter_path):
                continue
            
            for file in os.listdir(chapter_path):
                if file.endswith('.mp3'):
                    mp3_path = os.path.join(chapter_path, file)
                    
                    if os.path.getsize(mp3_path) == 0:
                        print(f"Warning: Skipping empty file: {mp3_path}")
                        continue
                    
                    duration = AudioSegment.from_mp3(mp3_path).duration_seconds
                    
                    if assigned_duration + duration <= max_duration_per_processor or i == nbr_pre_processors:
                        chapters.append(chapter)
                        assigned_duration += duration
                    else:
                        assignment[f"pre_processor_{i}"][book] = chapters
                        assignment[f"pre_processor_{i}"]["total_duration_hours"] = assigned_duration / 3600  # Convert seconds to hours
                        i += 1
                        chapters = []
                        assigned_duration = duration
                        chapters.append(chapter)

        if len(chapters) == len(os.listdir(book_path)):
            assignment[f"pre_processor_{i}"][book] = "all"
        else:
            assignment[f"pre_processor_{i}"][book] = chapters
    
            
    assignment[f"pre_processor_{nbr_pre_processors}"]["total_duration_hours"] = assigned_duration / 3600  # Convert seconds to hours

    # print(assignment)    
    
    with open(f'{data_path}/assignment.json', 'w', encoding='utf-8') as f:
        json.dump(assignment, f, indent=4)



if __name__ == '__main__':
    parser = create_base_parser('Assign data to pre-processors based on total duration.')
    parser.add_argument(
        '--nbr_pre_processors',
        type=int,
        default=5,
        help='Number of pre-processors to assign data to.'
    )
    args = parser.parse_args()
    
    assign_data_to_pre_processors(args.data_folder, args.nbr_pre_processors)
