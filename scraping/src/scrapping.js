const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { downloadText } = require('./textDownloader');
const { downloadAudio } = require('./audioDownloader');

const baseUrlAudio = 'https://www.bible.com/audio-bible/1854/MAT.1.NTE12';
const downloadFolder = '../data';

if (!fs.existsSync(downloadFolder)) {
    fs.mkdirSync(downloadFolder, { recursive: true });
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

async function processChapter(page, counter) {
    // We start on the AUDIO page
    const audioUrl = page.url();
    // Derive the TEXT page URL
    const textUrl = audioUrl.replace('/audio-bible/', '/bible/');

    console.log(`Switching to text version for scraping: ${textUrl}`);
    await page.goto(textUrl);

    const info = await getBookTitleAndChapter(page);
    console.log(`Current position: ${info ? `${info.book} ${info.chapter}` : 'Unknown'}`);

    let bookName = info ? info.book.replace(/[\s.]+/g, '_').toLowerCase() : 'unknown';
    let chapterNum = info ? info.chapter : counter;
    let fileNameBase = `${bookName}_${chapterNum}`;

    // Create nested folder structure: data/book/book_chapter/
    const bookPath = path.join(downloadFolder, bookName);
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

    // 3. Move to next chapter (this stays in the /audio-bible/ context)
    await navigateToNextPage(page);
    await page.waitForTimeout(3000);
}

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    await page.goto(baseUrlAudio);

    let counter = 1;
    while (counter <= 100) {
        console.log(`Processing chapter ${counter}...`);
        try {
            await processChapter(page, counter);
        } catch (err) {
            console.error(`Stopped at counter ${counter} due to error.`);
            break;
        }
        counter++;
    }

    await page.close();
    await browser.close();
})();
