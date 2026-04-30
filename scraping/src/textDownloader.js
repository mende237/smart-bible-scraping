const fs = require('fs');
const path = require('path');

async function downloadText(page, fileNameBase, downloadFolder) {
    const textContent = await page.evaluate(() => {
        const reader = document.querySelector('.ChapterContent-module__cat7xG__reader');
        if (!reader) return null;

        // Clone to avoid modifying the live page
        const clone = reader.cloneNode(true);
        
        // Remove notes/footnotes if they exist to keep text clean
        const notes = clone.querySelectorAll('.ChapterContent-module__cat7xG__note');
        notes.forEach(note => note.remove());

        // Process verses to maintain structure (verse number + text)
        const verses = clone.querySelectorAll('.ChapterContent-module__cat7xG__verse');
        let fullText = '';
        
        // Add Title
        const h1 = clone.querySelector('h1');
        if (h1) fullText += h1.innerText + '\n\n';

        verses.forEach(verse => {
            const label = verse.querySelector('.ChapterContent-module__cat7xG__label');
            const contents = verse.querySelectorAll('.ChapterContent-module__cat7xG__content');
            
            let verseText = '';
            if (label) {
                const labelText = label.innerText.trim();
                if (labelText) verseText += `[${labelText}] `;
            }
            
            contents.forEach(c => {
                verseText += c.innerText;
            });
            
            if (verseText.trim()) {
                fullText += verseText.trim() + '\n';
            }
        });

        // Fallback if specific verse structure isn't found
        if (!fullText.trim()) {
            return clone.innerText.trim();
        }

        return fullText;
    });

    if (textContent) {
        const textFilePath = path.join(downloadFolder, `${fileNameBase}.txt`);
        fs.writeFileSync(textFilePath, textContent);
        console.log(`Saved text version to ${textFilePath}`);
        return true;
    } else {
        console.log('Could not extract text content.');
        return false;
    }
}

module.exports = { downloadText };
