const { exec } = require('child_process');
const path = require('path');

async function downloadAudio(page, fileNameBase, downloadFolder) {
    const audioSrc = await page.evaluate(() => {
        const audioElement = document.querySelector('audio');
        return audioElement ? audioElement.src : null;
    });

    if (audioSrc) {
        const outputFileName = `${fileNameBase}.mp3`;
        const outputFilePath = path.join(downloadFolder, outputFileName);

        // Download the audio file using wget
        return new Promise((resolve, reject) => {
            exec(`wget -O ${outputFilePath} ${audioSrc}`, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error downloading audio: ${error}`);
                    reject(error);
                    return;
                }
                console.log(`Downloaded audio to ${outputFilePath}`);
                resolve(true);
            });
        });
    } else {
        console.log('No audio element found on the page.');
        return false;
    }
}

module.exports = { downloadAudio };
