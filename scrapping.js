const { chromium } = require('playwright');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const baseUrl = 'https://www.bible.com/audio-bible/905/MAT.1.FBDC';  // Replace with the actual URL
const downloadFolder = '/home/robinson/Downloads/Notebooks/notebooks_venv/Audio_conversations';  // Specify the folder where you want to save the downloaded files



if (!fs.existsSync(downloadFolder)) {
    fs.mkdirSync(downloadFolder, { recursive: true });
}

// Function to download audio and click the next button
async function downloadAudioAndProceed(page, counter) {
    const audioSrc = await page.evaluate(() => {
        const audioElement = document.querySelector('audio');
        return audioElement ? audioElement.src : null;
    });

    if (audioSrc) {
        const outputFileName = `matio_${counter}.mp3`;
        const outputFilePath = path.join(downloadFolder, outputFileName);

        // Download the audio file using wget
        exec(`wget -O ${outputFilePath} ${audioSrc}`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error downloading audio: ${error}`);
                return;
            }
            console.log(`Downloaded audio to ${outputFilePath}`);
        });
    } else {
        console.log('No audio element found on the page.');
    }

    // Click the next button
    await page.click('svg[aria-label="Next chapter"]');

    // Wait for a short while to ensure the next page loads
    await page.waitForTimeout(3000);
}

// Iterate over the URLs and perform the actions
(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    await page.goto(baseUrl);

    let counter = 1;
    while (counter <= 100) {  // Set the number of iterations as needed
        await downloadAudioAndProceed(page, counter);
        counter++;
    }

    await page.close();
    await browser.close();
})();
