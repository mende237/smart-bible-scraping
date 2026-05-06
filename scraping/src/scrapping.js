const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { downloadText } = require('./textDownloader');
const { downloadAudio } = require('./audioDownloader');

const language = "french"; // Change to "ewondo" for Ewondo language. This will set the correct version code and ID for the Bible.
let reachLastBooKToStop = false; // Set to true if you want to stop when the book changes (e.g. from MAT to MRK)

let versionCode = 'S21'; // Bible version code: NTE12 for ewondo; S21 for french
let versionId = '152';   // Bible version numeric ID: 1854 for ewondo; 152 for french
let downloadFolder = '../data/ewondo';
let shouldDownloadText = true;
let shouldDownloadAudio = false;


if (language === "french") {
    versionCode = 'S21';
    versionId = '152';
    // downloadFolder = '../data/default';
    shouldDownloadText = true;
    shouldDownloadAudio = false;
} else if (language === "ewondo") {
    versionCode = 'NTE12';
    versionId = '1854';
    // downloadFolder = '../data/default';
    shouldDownloadText = true;
    shouldDownloadAudio = true;
}

/**
 * CONFIGURATION
 * Edit these values to target specific books or chapters.
 */
const config = {
    bookCode: 'MAT',     // USFM code: MAT (Matthew), MRK (Mark), LUK (Luke), JHN (John), etc.
    startChapter: 1,     // Chapter to start from
    versionCode,
    versionId,
    downloadFolder,
    maxIterations: 100,  // Safety limit if downloadUntilEnd is false
    stopAtBookEnd: true, // Stop when the book changes (e.g. MAT -> MRK)
    downloadUntilEnd: true, // If true, ignore stopAtBookEnd and maxIterations, keep going until no "Next" button
    shouldDownloadText,
    shouldDownloadAudio,
    stopBookCode: 'REV' // Optional: If set, will stop when it reaches this book (e.g. "MRK" for Mark)
};

// Construct the initial URLs based on configuration
const baseUrlAudio = `https://www.bible.com/audio-bible/${config.versionId}/${config.bookCode}.${config.startChapter}.${config.versionCode}`;
const baseUrlText = `https://www.bible.com/bible/${config.versionId}/${config.bookCode}.${config.startChapter}.${config.versionCode}`;

const initialUrl = config.shouldDownloadAudio ? baseUrlAudio : baseUrlText;

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

    // Scroll to the bottom of the page first, as the button might be lazy-loaded or at the end of the content
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);

    // List of strategies to find and click the "Next Chapter" button
    const strategies = [
        {
            name: 'getByRole link with name "Next Chapter"',
            action: async () => await page.getByRole('link', { name: 'Next Chapter' }).first().click({ timeout: 5000 })
        },
        {
            name: 'getByLabel "Next Chapter"',
            action: async () => await page.getByLabel('Next Chapter').first().click({ timeout: 5000 })
        },
        {
            name: 'CSS selector a:has(svg title:has-text("Next Chapter"))',
            action: async () => await page.locator('a:has(svg title:has-text("Next Chapter"))').first().click({ timeout: 5000 })
        },
        {
            name: 'CSS selector svg title:has-text("Next Chapter")',
            action: async () => await page.locator('svg title:has-text("Next Chapter")').first().click({ timeout: 5000 })
        },
        {
            name: 'Aria-labelledby fallback',
            action: async () => await page.locator('[aria-labelledby*="Next"][aria-labelledby*="Chapter"]').first().click({ timeout: 5000 })
        },
        {
            name: 'XPath fallback for Next Chapter text',
            action: async () => await page.locator('//a[.//text()="Next Chapter"] | //button[.//text()="Next Chapter"]').first().click({ timeout: 5000 })
        }
    ];

    for (const strategy of strategies) {
        try {
            await strategy.action();
            console.log(`Clicked Next Chapter button using strategy: ${strategy.name}`);
            return;
        } catch (error) {
            // Strategy failed, move to next one
            // console.error(`${strategy.name} failed: ${error.message}`);
        }
    }

    // If all else fails, try to find a link that looks like a "next" link (contains next chapter number)
    // This is more complex and depends on knowing the current book/chapter.
    // For now, we throw an error if all strategies fail.
    throw new Error('All attempts to click Next Chapter button failed.');
}

async function processChapter(page, counter, initialBookCode) {
    const currentUrl = page.url();
    let audioUrl, textUrl;

    if (currentUrl.includes('/audio-bible/')) {
        audioUrl = currentUrl;
        textUrl = currentUrl.replace('/audio-bible/', '/bible/');
    } else {
        textUrl = currentUrl;
        audioUrl = currentUrl.replace('/bible/', '/audio-bible/');
    }

    // Extract book code from URL (e.g., https://.../MAT.1.S21 -> MAT)
    const urlParts = currentUrl.split('/');
    const biblePart = urlParts[urlParts.length - 1];
    const bookCode = biblePart.split('.')[0];

    // 1. Get Metadata (Book and Chapter)
    // We can get this from either page, but let's ensure we are on one of them
    const info = await getBookTitleAndChapter(page);
    if (!info) {
        throw new Error('Could not find book/chapter info on page.');
    }

    console.log(`Current position: ${info.book} ${info.chapter}`);

    if (config.stopBookCode && bookCode === config.stopBookCode) {
        console.log(`Reached stopBookCode ${config.stopBookCode}.`);
        reachLastBooKToStop = true;
    }

    if (reachLastBooKToStop && bookCode !== config.stopBookCode) {
        console.log(`Book changed from ${config.stopBookCode} to ${bookCode}. Stopping.`);
        return { shouldStop: true };
    }

    // Check if we should stop because the book changed
    if (!config.downloadUntilEnd && config.stopAtBookEnd && initialBookCode && bookCode !== initialBookCode) {
        console.log(`Book changed from ${initialBookCode} to ${bookCode}. Stopping.`);
        return { shouldStop: true };
    }

    let fileNameBase = `${bookCode}_${info.chapter}`;

    // Create nested folder structure: data/bookCode/bookCode_chapter/
    const bookPath = path.join(config.downloadFolder, bookCode);
    const chapterPath = path.join(bookPath, fileNameBase);

    if (!fs.existsSync(chapterPath)) {
        fs.mkdirSync(chapterPath, { recursive: true });
    }


    // 3. Download Audio if requested
    if (config.shouldDownloadAudio) {
        if (!page.url().includes('/audio-bible/')) {
            console.log(`Switching back to audio version: ${audioUrl}`);
            await page.goto(audioUrl);
        }
        await downloadAudio(page, `${fileNameBase}_${language}`, chapterPath);
    }

    // 2. Download Text if requested
    if (config.shouldDownloadText) {
        if (!page.url().includes('/bible/')) {
            console.log(`Switching to text version: ${textUrl}`);
            await page.goto(textUrl);
        }
        await downloadText(page, `${fileNameBase}_${language}`, chapterPath);
    }


    // 4. Move to next chapter
    await navigateToNextPage(page);
    await page.waitForTimeout(3000);

    return { shouldStop: false, currentBookCode: bookCode };
}

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    console.log(`Starting download from: ${initialUrl}`);
    await page.goto(initialUrl);

    let counter = 1;
    let initialBookCode = null;
    const loopLimit = config.downloadUntilEnd ? Infinity : config.maxIterations;

    while (counter <= loopLimit) {
        console.log(`\n--- Iteration ${counter} ---`);
        try {
            const result = await processChapter(page, counter, initialBookCode);

            if (result.shouldStop) {
                break;
            }

            // Set the initial book name on the first successful iteration
            if (!initialBookCode) {
                initialBookCode = result.currentBookCode;
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
