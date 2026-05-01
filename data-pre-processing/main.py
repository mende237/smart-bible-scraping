import os
import json
import shutil

def getBookTitles(folder_path):
    bookTitles = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
    
    with open("map/book-title-mapping.json", "w") as f:
        json.dump({title: [] for title in bookTitles}, f)
        
        
def mapBookWithFrenchVersion(data_folder):
    mapper = readBookTitleMappingFinal()
    for book in os.listdir(os.path.join(data_folder, "ewondo")):
        mapping = mapper.get(book, [])
        for mapped_book in mapping:
            if os.path.exists(os.path.join(data_folder, "french", mapped_book)):
                print(f"Mapping found for {book}: {mapped_book}")
                for chapter in os.listdir(os.path.join(data_folder, "french", mapped_book)):
                    chapter_number = chapter.split("_")[-1] 
                    if chapter_number is None:
                        print(f"Warning: Could not extract chapter number from file name '{file}' in book '{mapped_book}'. Skipping this file.")
                        continue
                    for file in os.listdir(os.path.join(data_folder, "french", mapped_book, chapter)):
                        if file.endswith('.txt'):
                            print(f"Extracted chapter number '{chapter_number}' from file name '{file}' in book '{mapped_book}'.")
                            ewondo_chapter_folder_path = os.path.join(data_folder, "ewondo", book, f"{book}_{chapter_number}", f"{book}_{chapter_number}_fr.txt")
                            french_file_path = os.path.join(data_folder, "french", mapped_book, f"{mapped_book}_{chapter_number}", file)
                            shutil.copy(french_file_path, ewondo_chapter_folder_path)


def readBookTitleMappingFinal(file_path="map/book-title-mapping-final.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# getBookTitles("../scraping/data/ewondo")

mapBookWithFrenchVersion("../scraping/data")


