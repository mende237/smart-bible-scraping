# Bible Scraper & Data Pre-processor

A modular toolkit designed to scrape audio and text versions of the Bible from [Bible.com](https://www.bible.com) and pre-process the data for ASR (Automatic Speech Recognition) or other NLP tasks.

## Project Structure

- `scraping/`: Node.js tool powered by **Playwright** to automatically download text and audio versions of chapters.
- `data-pre-processing/`: Python scripts to organize, clean, and map scraped data.
- `data-verification/`: Modular Python scripts to verify transcriptions against expected original text and log errors.
- `data-synchronisation/`: A modular synchronization package to sync local data with Google Drive, including mandatory verification gates.
- `utils/`: Helper scripts for data analysis and task distribution.

## 1. Scraping Module

### Features
- **Dual Format**: Downloads both `.txt` (clean verses) and `.mp3` (audio) for every chapter.
- **Smart Organization**: Automatically groups files into nested folders: `data/<language>/<book>/<book_chapter>/`.
- **Targeted Scraping**: Configure specific books, starting chapters, or versions. Option to download only a single chapter.
- **Customizable Settings**: Extensive command-line arguments for dynamic scraping (`--language`, `--book`, `--chapter`, `--suffix`, `--text-only`, `--single-chapter`, `--download-folder`).
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

   # Example: Download to a custom folder:
   node src/scrapping.js --download-folder /path/to/custom/folder
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

# You can also process a specific chapter:
python pre_process_verses.py --book MAT --chapter MAT_1
# 3. Create verse sub-folders
python generate_verses_folder.py --data_folder ../scraping/data/ewondo
# 4. Monitor for new audio segments (run in background during segmentation)
python generate_utterance_file.py --data_folder ../scraping/data/ewondo
```

## 3. Data Verification Module

### Features
- **Automated Verification**: Compares segmented audio transcriptions against the original scraped text to ensure accuracy.
- **Auto-Recovery**: Automatically downloads and pre-processes missing reference text from Bible.com if it's not found in the local data folder.
- **Modular Design**: Refactored into `validator.py` (core logic), `utils.py` (helpers), and `verify_data.py` (CLI entry point).
- **Granular Control**: Supports verification at the verse, chapter, book, or preprocessor assignment level.
- **Detailed Logging**: Logs all mismatches and missing files to `data-verification/logs/verification_errors.log`.
- **Exit Codes**: Returns `0` on success and `1` on failure, allowing integration into automated workflows.

### Usage
```bash
cd data-verification
# Verify a specific preprocessor's workload (requires assignment.json)
python verify_data.py --preprocessor pre_processor_1

# Verify a specific book
python verify_data.py --book MAT

# Verify a specific chapter
python verify_data.py --book MAT --chapter MAT_1

# Verify a specific verse
python verify_data.py --book MAT --chapter MAT_1 --verse V_1
```

## 4. Utilities Module

### Scripts
- **`data_statistics.py`**: Analyzes the scraped data to generate `statistics.json`, containing metrics like total books, chapters, verses, and audio duration (mean, median, max, min) for each language.
- **`assigning_data_to_pre_pocessors.py`**: Distributes the workload among a specified number of "pre-processors" by balancing the total audio duration assigned to each. It generates an `assignment.json` file.

### Usage
```bash
cd utils
# Generate data statistics
python data_statistics.py --data_folder ../scraping/data/ewondo
# Assign data to 5 pre-processors
python assigning_data_to_pre_pocessors.py --data_folder ../scraping/data/ewondo --nbr_pre_processors 5
```

## 5. Data Synchronisation Module

### Features
- **Cloud Backup**: Synchronizes local data with Google Drive to ensure work is safely backed up and accessible.
- **Verification Gate**: Automated verification before synchronization.
- **Partial Sync**: **Smart synchronization logic** that skips individual verses that fail verification while still uploading those that pass.
- **Preprocessor Support**: Effortlessly synchronize an entire workload assigned to a specific preprocessor.
- **Granular Sync**: Supports synchronization at the book, chapter, or verse level.
- **Dual Authentication**: Supports both **Service Accounts** and **OAuth2 User Authentication** (recommended to use your personal storage quota).
- **Headless Mode**: Special flag for authenticating on remote servers without browser access.
- **Modular Package**: Refactored into `config.py`, `auth.py`, `synchronizer.py`, and `synchronise_data.py`.

### Setup
1. **Create a Google Cloud Project:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project (e.g., "Smart-Transcribe").
2. **Enable Google Drive API:**
   - Navigate to **APIs & Services > Library**.
   - Search for "Google Drive API" and click **Enable**.
3. **Configure OAuth Consent Screen (Required for OAuth2):**
   - Go to **APIs & Services > OAuth consent screen**.
   - Choose **External** and fill in the required app information.
   - **Test Users (Crucial):** Scroll down to "Test users" and add **every Gmail address** (yours and your collaborators') that will use the script. 
     - *Note:* If an email is not added here, the user will get an **"Error 403: access_denied"** when trying to log in.
   - **Note on Security Warning:** Since the app is not verified by Google, you will see a "Google hasn't verified this app" message during the first login. Click **Advanced** and then **Go to [Your Project Name] (unsafe)** to proceed.
4. **Obtain Credentials:**
   - **For `client-secret.json` (Personal Quota - Recommended):**
     - Go to **APIs & Services > Credentials**.
     - Click **Create Credentials > OAuth client ID**.
     - Select **Desktop app**, name it, and download the JSON.
     - Rename it to `client-secret.json` and place it in the `account/` folder.
   - **For `service-account.json` (Optional):**
     - Click **Create Credentials > Service Account**.
     - Follow the steps to create it, then go to the **Keys** tab of the new account.
     - Click **Add Key > Create new key (JSON)**.
     - Rename the downloaded file to `service-account.json` and place it in the `account/` folder.
5. **Configure Environment:**
   - Configure your target Drive folder in the `.env` file:
     ```env
     DRIVE_FOLDER_ID=your_folder_id_here
     ```
   - **Sharing:** Ensure the target Google Drive folder is **shared** with the email address of the Service Account (if used) or that your personal account has "Editor" access to it.

### Usage
```bash
cd data-synchronisation

# Synchronize a specific preprocessor's workload (Verify then Sync)
python synchronise_data.py --preprocessor pre_processor_1

# Synchronize a specific book
python synchronise_data.py --book MAT

# Synchronize a specific chapter
python synchronise_data.py --book MAT --chapter MAT_1

# Synchronize a specific verse
python synchronise_data.py --book MAT --chapter MAT_1 --verse V_1

# Skip verification gate (Force Sync)
python synchronise_data.py --book MAT --no-verify

# Synchronize on a remote server (SSH)
python synchronise_data.py --book MAT --headless
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
