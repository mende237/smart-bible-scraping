const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { downloadText } = require('./textDownloader');
const { downloadAudio } = require('./audioDownloader');

/**
 * CONFIGURATION
 * Edit these values to target specific books or chapters.
 */
const config = {
    bookCode: 'JUD',     // USFM code: MAT (Matthew), MRK (Mark), LUK (Luke), JHN (John), etc.
    startChapter: 1,     // Chapter to start from
    versionCode: 'NTE12',// Bible version code
    versionId: '1854',   // Bible version numeric ID
    downloadFolder: '../data',
    maxIterations: 100,  // Safety limit if downloadUntilEnd is false
    stopAtBookEnd: true, // Stop when the book changes (e.g. MAT -> MRK)
    downloadUntilEnd: true // If true, ignore stopAtBookEnd and maxIterations, keep going until no "Next" button
};

// Construct the initial URL based on configuration
const baseUrlAudio = `https://www.bible.com/audio-bible/${config.versionId}/${config.bookCode}.${config.startChapter}.${config.versionCode}`;

if (!fs.existsSync(config.downloadFolder)) {
    fs.mkdirSync(config.downloadFolder, { recursive: true });
}

async function getBookTitleAndChapter(page) {
    return await page.evaluate(() => {
        // Try to find the H1 in the reader (text page) or the specific header (audio page)
        const h1 = document.querySelector('.ChapterContent-module__cat7xG__reader h1') ||
            document.querySelector('h1.text-text-light')

        if (h1) {
            // Remove "Listen to" if present (audio page) and trim
            const text = h1.innerText.replace('Listen to', '').trim();

            // Split by space. The last part is usually the chapter number.
            const parts = text.split(' ');
            if (parts.length >= 2) {
                const chapter = parts.pop();
                const book = parts.join(' ');
                return { book, chapter };
            }
            return { book: text, chapter: '' };
        }
        return null;
    });
}

async function navigateToNextPage(page) {
    console.log('Attempting to click Next Chapter button...');
    const nextButton = page.getByLabel('Next Chapter');
    try {
        await nextButton.click({ timeout: 30000 });
        console.log('Clicked Next Chapter button.');
    } catch (error) {
        console.error('Failed to click Next Chapter button with getByLabel:', error.message);
        try {
            await page.click('[aria-label="Next Chapter"]', { timeout: 10000 });
            console.log('Clicked Next Chapter button (fallback).');
        } catch (fallbackError) {
            console.error('Fallback also failed.');
            throw fallbackError;
        }
    }
}

async function processChapter(page, counter, initialBookName) {
    // We start on the AUDIO page
    const audioUrl = page.url();
    // Derive the TEXT page URL
    const textUrl = audioUrl.replace('/audio-bible/', '/bible/');

    console.log(`Switching to text version for scraping: ${textUrl}`);
    await page.goto(textUrl);

    const info = await getBookTitleAndChapter(page);
    if (!info) {
        throw new Error('Could not find book/chapter info on page.');
    }

    console.log(`Current position: ${info.book} ${info.chapter}`);

    // Check if we should stop because the book changed
    // ONLY check this if downloadUntilEnd is false
    if (!config.downloadUntilEnd && config.stopAtBookEnd && initialBookName && info.book !== initialBookName) {
        console.log(`Book changed from ${initialBookName} to ${info.book}. Stopping.`);
        return { shouldStop: true };
    }

    let bookNameSafe = info.book.replace(/[\s.]+/g, '_').toLowerCase();
    let fileNameBase = `${bookNameSafe}_${info.chapter}`;

    // Create nested folder structure: data/book/book_chapter/
    const bookPath = path.join(config.downloadFolder, bookNameSafe);
    const chapterPath = path.join(bookPath, fileNameBase);

    if (!fs.existsSync(chapterPath)) {
        fs.mkdirSync(chapterPath, { recursive: true });
    }

    // 1. Download Text from the /bible/ URL
    await downloadText(page, fileNameBase, chapterPath);

    // 2. Switch back to Audio Page to get the MP3
    console.log(`Switching back to audio version: ${audioUrl}`);
    await page.goto(audioUrl);
    await downloadAudio(page, fileNameBase, chapterPath);

    // 3. Move to next chapter
    await navigateToNextPage(page);
    await page.waitForTimeout(3000);

    return { shouldStop: false, currentBookName: info.book };
}

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    console.log(`Starting download from: ${baseUrlAudio}`);
    await page.goto(baseUrlAudio);

    let counter = 1;
    let initialBookName = null;
    const loopLimit = config.downloadUntilEnd ? Infinity : config.maxIterations;

    while (counter <= loopLimit) {
        console.log(`\n--- Iteration ${counter} ---`);
        try {
            const result = await processChapter(page, counter, initialBookName);

            if (result.shouldStop) {
                break;
            }

            // Set the initial book name on the first successful iteration
            if (!initialBookName) {
                initialBookName = result.currentBookName;
            }
        } catch (err) {
            console.log(`Stopping: No more chapters found or error occurred: ${err.message}`);
            break;
        }
        counter++;
    }

    await page.close();
    await browser.close();
    console.log('\nProcessing complete.');
})();
