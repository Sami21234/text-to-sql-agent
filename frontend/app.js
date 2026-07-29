const API = 'http://localhost:8000';

const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const askBtnText = document.getElementById('askBtnText');
const resultsArea = document.getElementById('resultsArea');
const chipsContainer = document.getElementById('chipsContainer');
const historyList = document.getElementById('historyList');
const historyCount = document.getElementById('historyCount');
const uploadStatus = document.getElementById('uploadStatus');
const dbTables = document.getElementById('dbTables');
const headerMeta = document.getElementById('headerMeta');
const dbFileInput = document.getElementById('dbFileInput');
const uploadBox = document.getElementById('uploadBox');


// Drag and drop support
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('drag-over');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('drag-over');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
});

dbFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFileUpload(file);
});


// Upload a database file
async function handleFileUpload(file) {
    if (!file.name.endsWith('.db')) {
        uploadStatus.textContent = 'Error: Only .db files supported';
        return;
    }

    uploadStatus.textContent = `Uploading ${file.name}...`;
    chipsContainer.innerHTML =
        '<div class="chip-loading">Generating questions...</div>';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API}/upload-db`, {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (!res.ok) {
            uploadStatus.textContent = `Error: ${data.detail}`;
            return;
        }

        uploadStatus.textContent = `Using: ${data.filename}`;
        headerMeta.textContent = `${data.filename} — ${Object.keys(data.tables).length} tables`;

        // Show table info
        dbTables.innerHTML = Object.entries(data.tables).map(
            ([name, count]) => `
            <div class="db-table-row">
                <span class="db-table-name">📋 ${name}</span>
                <span class="db-table-count">${count} rows</span>
            </div>
        `).join('');

        // Clear results and history
        resultsArea.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✅</div>
                <div class="empty-title">Database loaded</div>
                <div class="empty-text">
                    ${data.message}
                </div>
            </div>`;

        historyList.innerHTML =
            '<div class="history-empty">No queries yet</div>';
        historyCount.textContent = '0';

        // Poll for sample questions
        setTimeout(loadSampleQuestions, 3000);

    } catch (err) {
        uploadStatus.textContent = 'Upload failed. Try again.';
    }
}


// Load sample questions
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
            '<div class="chip-loading">Could not load suggestions</div>';
    }
}


// Show loading card
function showLoading() {
    const empty = resultsArea.querySelector('.empty-state');
    if (empty) empty.remove();

    const card = document.createElement('div');
    card.className = 'loading-card';
    card.id = 'loadingCard';
    card.innerHTML = `
        <div class="spinner"></div>
        <span>Writing SQL and querying database...</span>
    `;
    resultsArea.insertBefore(card, resultsArea.firstChild);
}

function removeLoading() {
    const card = document.getElementById('loadingCard');
    if (card) card.remove();
}


// Add result card
function addResult(question, answer, sql, historyId, isError = false) {
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

    const exportBtn = historyId !== undefined ? `
        <button
            class="history-export"
            onclick="exportCSV(${historyId})"
            title="Export to CSV"
        >⬇ CSV</button>
    ` : '';

    card.innerHTML = `
        <div class="result-header">
            <span>${escapeHtml(question)}</span>
            ${exportBtn}
        </div>
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


// Export to CSV
async function exportCSV(historyId) {
    try {
        const res = await fetch(`${API}/export/${historyId}`);

        if (!res.ok) {
            alert('Export failed. The query may not return tabular data.');
            return;
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `querypilot_export_${historyId}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (err) {
        alert('Export failed. Please try again.');
    }
}


// Update history panel
function updateHistory(question, historyId) {
    const empty = historyList.querySelector('.history-empty');
    if (empty) empty.remove();

    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = `
        <span class="history-question"
              title="${escapeHtml(question)}">
            ${escapeHtml(question)}
        </span>
        <button
            class="history-export"
            onclick="exportCSV(${historyId})"
            title="Export to CSV"
        >⬇</button>
    `;

    item.addEventListener('click', (e) => {
        if (e.target.classList.contains('history-export')) return;
        questionInput.value = question;
        questionInput.focus();
    });

    historyList.insertBefore(item, historyList.firstChild);
    historyCount.textContent =
        parseInt(historyCount.textContent) + 1;
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
    showLoading();

    try {
        const res = await fetch(`${API}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await res.json();
        removeLoading();

        if (!res.ok) {
            addResult(question, `Error: ${data.detail}`, '', undefined, true);
            return;
        }

        addResult(question, data.answer, data.sql, data.history_id);
        updateHistory(question, data.history_id);
        questionInput.value = '';

    } catch (err) {
        removeLoading();
        addResult(
            question,
            'Failed to connect. Is the server running?',
            '',
            undefined,
            true
        );
    } finally {
        askBtn.disabled = false;
        askBtnText.textContent = 'Ask';
        questionInput.focus();
    }
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(text)));
    return div.innerHTML;
}


// Reset to demo database
document.getElementById('resetBtn').addEventListener('click', async () => {
    try {
        await fetch(`${API}/reset`, { method: 'DELETE' });
        uploadStatus.textContent = 'Using: food_delivery.db (demo)';
        headerMeta.textContent = 'Food Delivery Analytics';
        dbTables.innerHTML = '';
        resultsArea.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💬</div>
                <div class="empty-title">Ask anything about your data</div>
                <div class="empty-text">
                    Reset to demo database. Ask a question to get started.
                </div>
            </div>`;
        historyList.innerHTML =
            '<div class="history-empty">No queries yet</div>';
        historyCount.textContent = '0';
        loadSampleQuestions();
    } catch (err) {
        console.error('Reset failed', err);
    }
});


// Event listeners
askBtn.addEventListener('click', askQuestion);

questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});


// Init
loadSampleQuestions();