const API = 'http://localhost:8000';

const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const askBtnText = document.getElementById('askBtnText');
const resultsArea = document.getElementById('resultsArea');
const chipsContainer = document.getElementById('chipsContainer');


// Load sample questions on page load
async function loadSampleQuestions() {
    try {
        const res = await fetch(`${API}/sample-questions`);
        const data = await res.json();

        chipsContainer.innerHTML = '';

        data.questions.forEach(question => {
            const chip = document.createElement('button');
            chip.className = 'chip';
            chip.textContent = question;
            chip.addEventListener('click', () => {
                questionInput.value = question;
                questionInput.focus();
            });
            chipsContainer.appendChild(chip);
        });

    } catch (err) {
        chipsContainer.innerHTML =
            '<div class="chip-loading">Could not load suggestions.</div>';
    }
}


// Add loading card
function showLoading(question) {
    // Remove empty state if present
    const empty = resultsArea.querySelector('.empty-state');
    if (empty) empty.remove();

    const card = document.createElement('div');
    card.className = 'loading-card';
    card.id = 'loadingCard';
    card.innerHTML = `
        <div class="spinner"></div>
        <span>Generating SQL and querying database...</span>
    `;
    resultsArea.insertBefore(card, resultsArea.firstChild);
}


function removeLoading() {
    const card = document.getElementById('loadingCard');
    if (card) card.remove();
}


// Add result card
function addResult(question, answer, sql, isError = false) {
    const card = document.createElement('div');
    card.className = 'result-card';

    const sqlSection = sql ? `
        <div class="sql-panel">
            <button class="sql-toggle" onclick="toggleSQL(this)">
                ▶ Show SQL Query
            </button>
            <div class="sql-code">${escapeHtml(sql)}</div>
        </div>
    ` : '';

    card.innerHTML = `
        <div class="result-question">${escapeHtml(question)}</div>
        <div class="result-answer ${isError ? 'error' : ''}">
            ${escapeHtml(answer)}
        </div>
        ${sqlSection}
    `;

    resultsArea.insertBefore(card, resultsArea.firstChild);
}


function toggleSQL(btn) {
    const code = btn.nextElementSibling;
    const isVisible = code.classList.contains('visible');
    code.classList.toggle('visible');
    btn.textContent = isVisible
        ? '▶ Show SQL Query'
        : '▼ Hide SQL Query';
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}


// Ask a question
async function askQuestion() {
    const question = questionInput.value.trim();

    if (!question) {
        questionInput.focus();
        return;
    }

    askBtn.disabled = true;
    askBtnText.textContent = 'Thinking...';
    showLoading(question);

    try {
        const res = await fetch(`${API}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await res.json();
        removeLoading();

        if (!res.ok) {
            addResult(question, `Error: ${data.detail}`, '', true);
            return;
        }

        addResult(question, data.answer, data.sql);
        questionInput.value = '';

    } catch (err) {
        removeLoading();
        addResult(
            question,
            'Failed to connect to backend. Is the server running?',
            '',
            true
        );
    } finally {
        askBtn.disabled = false;
        askBtnText.textContent = 'Ask';
        questionInput.focus();
    }
}


// Event listeners
askBtn.addEventListener('click', askQuestion);

questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});


// Start
loadSampleQuestions();