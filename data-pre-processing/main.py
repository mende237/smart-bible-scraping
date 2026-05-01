import os
import json

def getBookTitles(folder_path):
    bookTitles = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
    
    with open("map/book-title-mapping.json", "w") as f:
        json.dump({title: [] for title in bookTitles}, f)
        
        
        


# getBookTitles("../scraping/data/ewondo")



