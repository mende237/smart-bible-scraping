# Bible Scraper & Data Pre-processor

A modular toolkit designed to scrape audio and text versions of the Bible from [Bible.com](https://www.bible.com) and pre-process the data for ASR (Automatic Speech Recognition) or other NLP tasks.

## Project Structure

- `scraping/`: Node.js tool powered by **Playwright** to automatically download text and audio versions of chapters.
- `data-pre-processing/`: Python scripts to organize and map scraped data (e.g., mapping French translations to Ewondo audio/text).

## 1. Scraping Module

### Features
- **Dual Format**: Downloads both `.txt` (clean verses) and `.mp3` (audio) for every chapter.
- **Modular Design**: Separate downloaders for text and audio for easy maintenance.
- **Smart Organization**: Automatically groups files into nested folders: `data/<language>/<book>/<book>_<chapter>/`.
- **Targeted Scraping**: Configure specific books, starting chapters, or versions.
- **Continuous Mode**: Optional "Download Until End" mode to scrape entire books or even the whole Bible automatically.

### Prerequisites
- [Node.js](https://nodejs.org/) (v14 or higher)
- `wget` installed on your system (used for audio downloads)

### Installation
1. Navigate to the scraping directory:
   ```bash
   cd scraping
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. (If first time) Install Playwright browsers:
   ```bash
   npx playwright install chromium
   ```

### Usage
To start the scraper:
```bash
node src/scrapping.js
```

### Configuration
Customize the scraping behavior in `scraping/src/scrapping.js`:
- `language`: 'french' or 'ewondo' (pre-configured presets).
- `bookCode`: USFM code (MAT, MRK, LUK, JHN, etc.).
- `downloadUntilEnd`: Set to `true` to scrape continuously.

## 2. Data Pre-processing Module

### Features
- **Book Title Mapping**: Generates and manages mappings between different language versions of Bible books.
- **Automated Copying**: Automatically copies French text versions into corresponding Ewondo chapter folders for alignment.

### Usage
The main script is `data-pre-processing/main.py`. It uses JSON maps in the `map/` directory to coordinate between versions.

1. Ensure your scraped data is in the `scraping/data/` folder.
2. Run the pre-processing script:
   ```bash
   cd data-pre-processing
   python main.py
   ```

### Folder Structure After Processing
```
scraping/data/
├── ewondo/
│   └── mat/
│       └── mat_1/
│           ├── mat_1.mp3      (Ewondo Audio)
│           ├── mat_1.txt      (Ewondo Text)
│           └── mat_1_fr.txt   (French Text - Copied by pre-processor)
└── french/
    └── mat/
        └── mat_1/
            └── mat_1.txt
```

## Troubleshooting

- **Timeout Error**: If you get a timeout, it might be due to slow page loads or a cookie consent popup blocking the script.
- **Selector Changes**: The scraper depends on specific CSS classes on Bible.com. If the site layout changes, the selectors in `src/scrapping.js` or `src/textDownloader.js` may need updating.
- **wget not found**: Ensure `wget` is available in your PATH. If you are on Windows, you may need to install it separately.
- **Mapping Errors**: Ensure `book-title-mapping-final.json` correctly maps the folder names from the `ewondo` directory to the `french` directory.
