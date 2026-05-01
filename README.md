# Bible Scraper (Audio & Text)

A modular Node.js tool powered by **Playwright** to automatically download text and audio versions of chapters from [Bible.com](https://www.bible.com).

## Features

- **Dual Format**: Downloads both `.txt` (clean verses) and `.mp3` (audio) for every chapter.
- **Modular Design**: Separate downloaders for text and audio for easy maintenance.
- **Smart Organization**: Automatically groups files into nested folders: `data/<book>/<book>_<chapter>/`.
- **Targeted Scraping**: Configure specific books, starting chapters, or versions.
- **Continuous Mode**: Optional "Download Until End" mode to scrape entire books or even the whole Bible automatically.

## Prerequisites

- [Node.js](https://nodejs.org/) (v14 or higher)
- `wget` installed on your system (used for audio downloads)

## Installation

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

## Usage

To start the scraper:
```bash
node src/scrapping.js
```

## Configuration

You can customize the scraping behavior by editing the `config` object in `src/scrapping.js`:

```javascript
const config = {
    bookCode: 'MAT',     // USFM code (MAT, MRK, LUK, JHN, etc.)
    startChapter: 1,     // Which chapter to start from
    versionCode: 'NTE12',// Bible version code (e.g., NTE12)
    versionId: '1854',   // Bible version numeric ID (e.g., 1854)
    downloadFolder: '../data',
    maxIterations: 100,  // Max chapters to scrape (safety limit)
    stopAtBookEnd: true, // Stop when the book changes (e.g., MAT -> MRK)
    downloadUntilEnd: false // Scrape continuously until no more chapters are found
};
```

## Folder Structure

Downloads are organized hierarchically:
```
data/
└── mat/
    └── mat_1/
        ├── mat_1.mp3
        └── mat_1.txt
    └── mat_2/
        ├── mat_2.mp3
        └── mat_2.txt
```

## Troubleshooting

- **Timeout Error**: If you get a timeout, it might be due to slow page loads or a cookie consent popup blocking the script.
- **Selector Changes**: The scraper depends on specific CSS classes on Bible.com. If the site layout changes, the selectors in `src/scrapping.js` or `src/textDownloader.js` may need updating.
- **wget not found**: Ensure `wget` is available in your PATH. If you are on Windows, you may need to install it separately or modify `src/audioDownloader.js` to use a different download method.
