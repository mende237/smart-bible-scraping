# Bible Scraper & Data Pre-processor

A modular toolkit designed to scrape audio and text versions of the Bible from [Bible.com](https://www.bible.com) and pre-process the data for ASR (Automatic Speech Recognition) or other NLP tasks.

## Project Structure

- `scraping/`: Node.js tool powered by **Playwright** to automatically download text and audio versions of chapters.
- `data-pre-processing/`: Python scripts to organize, clean, and map scraped data.
- `utils/`: Helper scripts for data analysis and task distribution.

## 1. Scraping Module

### Features
- **Dual Format**: Downloads both `.txt` (clean verses) and `.mp3` (audio) for every chapter.
- **Smart Organization**: Automatically groups files into nested folders: `data/<language>/<book>/<book_chapter>/`.
- **Targeted Scraping**: Configure specific books, starting chapters, or versions. Option to download only a single chapter.
- **Customizable Settings**: Extensive command-line arguments for dynamic scraping (`--language`, `--book`, `--chapter`, `--suffix`, `--text-only`, `--single-chapter`).
- **Continuous Mode**: Optional "Download Until End" mode to scrape entire books automatically.

### Prerequisites
- [Node.js](https://nodejs.org/) (v14 or higher)
- `wget` installed on your system (used for audio downloads)

### Usage
1. Navigate to the scraping directory and install dependencies:
   ```bash
   cd scraping
   npm install
   npx playwright install chromium
   ```
2. Start the scraper:
   ```bash
   node src/scrapping.js

   # You can also specify custom parameters:
   node src/scrapping.js --suffix original
   
   # Example: Download only the text for chapter 1 of Mark in Ewondo:
   node src/scrapping.js --language ewondo --book MRK --chapter 1 --text-only --single-chapter --suffix original
   ```

## 2. Data Pre-processing Module

### Scripts
- **`main.py`**: Coordinates between language versions. It uses JSON maps in `map/` to copy corresponding French text into Ewondo chapter folders for alignment.
- **`pre_process_verses.py`**: Cleans the scraped text files by merging multi-line verses and ensuring each verse starts on a new line with its number in brackets (e.g., `[1]`).
- **`generate_verses_folder.py`**: Creates individual sub-folders for each verse (e.g., `V_1`, `V_2`) within each chapter folder, based on the verse numbers found in the text files.
- **`generate_utterance_file.py`**: A monitoring script that watches the data directory for new `.wav` files (e.g., created during manual audio segmentation) and automatically generates matching empty `.txt` files for transcriptions.

### Usage
```bash
cd data-pre-processing
# 1. Map and copy French text to Ewondo folders
python main.py
# 2. Clean up verse formatting
python pre_process_verses.py --data_folder ../scraping/data/ewondo
# 3. Create verse sub-folders
python generate_verses_folder.py --data_folder ../scraping/data/ewondo
# 4. Monitor for new audio segments (run in background during segmentation)
python generate_utterance_file.py --data_folder ../scraping/data/ewondo
```

## 3. Utilities Module

### Scripts
- **`data_statistics.py`**: Analyzes the scraped data to generate `statistics.json`, containing metrics like total books, chapters, verses, and audio duration (mean, median, max, min) for each language.
- **`assigning_data_to_pre_pocessors.py`**: Distributes the workload among a specified number of "pre-processors" by balancing the total audio duration assigned to each. It generates an `assignement.json` file.

### Usage
```bash
cd utils
# Generate data statistics
python data_statistics.py --data_folder ../scraping/data/ewondo
# Assign data to 5 pre-processors
python assigning_data_to_pre_pocessors.py --data_folder ../scraping/data/ewondo --nbr_pre_processors 5
```

## Folder Structure After Processing
```
scraping/data/
├── ewondo/
│   └── MAT/
│       └── MAT_1/
│           ├── MAT_1.mp3      (Full Chapter Audio)
│           ├── MAT_1.txt      (Cleaned Ewondo Text)
│           ├── MAT_1_fr.txt   (French Text - for alignment)
│           ├── V_1/           (Verse-specific folder)
│           │   ├── V_1_UTT_1.wav  (Segmented Audio)
│           │   └── V_1_UTT_1.txt  (Utterance Transcription)
│           └── V_2/           ...
└── french/
    └── MAT/
        └── MAT_1/
            └── MAT_1.txt
```

## Troubleshooting

- **Timeout Error**: Might be due to slow page loads or cookie consent popups.
- **Selector Changes**: The scraper depends on Bible.com's CSS classes. If the site layout changes, update selectors in `src/scrapping.js` or `src/textDownloader.js`.
- **wget not found**: Ensure `wget` is available in your PATH.
- **Mapping Errors**: Check `map/book-title-mapping-final.json` for correct folder name mappings.
