document.addEventListener('DOMContentLoaded', () => {
    const simulatorCard = document.querySelector('#puzzle-simulator');
    if (!simulatorCard) return; // Only run if the simulator element exists on the page

    const puzzleTextEl = document.getElementById('sim-puzzle-text');
    const puzzleClueEl = document.getElementById('sim-puzzle-clue');
    const puzzleSolutionInput = document.getElementById('sim-solution-input');
    const puzzleCheckBtn = document.getElementById('sim-check-btn');
    const puzzleResultEl = document.getElementById('sim-result');
    const puzzleRefreshBtn = document.getElementById('sim-refresh-btn');

    let currentSolution = '';

    const generatePuzzle = () => {
        // Simple client-side puzzle generator
        const words = ["DISCOVERY", "CIPHER", "SECRET", "ORACLE", "GENESIS"];
        const solutionWord = words[Math.floor(Math.random() * words.length)];
        const solutionNumber = Math.floor(Math.random() * 900) + 100;
        currentSolution = `${solutionWord}${solutionNumber}`;

        const shiftKey = Math.floor(Math.random() * 22) + 3; // Shift between 3-24

        let encryptedText = "";
        for (const char of currentSolution) {
            if (char >= 'A' && char <= 'Z') {
                let shifted = char.charCodeAt(0) + shiftKey;
                if (shifted > 'Z'.charCodeAt(0)) {
                    shifted -= 26;
                }
                encryptedText += String.fromCharCode(shifted);
            } else {
                encryptedText += char;
            }
        }

        puzzleTextEl.textContent = `Decrypt the following text: '${encryptedText}'`;
        puzzleClueEl.textContent = `Clue: Caesar cipher, shift key = ${shiftKey}`;
        puzzleSolutionInput.value = '';
        puzzleResultEl.textContent = '';
        puzzleResultEl.className = 'sim-result';
    };

    const checkSolution = () => {
        const userAnswer = puzzleSolutionInput.value.trim().toUpperCase();
        if (userAnswer === currentSolution) {
            puzzleResultEl.textContent = 'Correct! You have what it takes to join The Hunt.';
            puzzleResultEl.className = 'sim-result correct';
        } else {
            puzzleResultEl.textContent = 'Incorrect. Try again.';
            puzzleResultEl.className = 'sim-result incorrect';
        }
    };

    puzzleCheckBtn.addEventListener('click', checkSolution);
    puzzleSolutionInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            checkSolution();
        }
    });
    puzzleRefreshBtn.addEventListener('click', generatePuzzle);

    // Generate the first puzzle when the page loads
    generatePuzzle();
});
