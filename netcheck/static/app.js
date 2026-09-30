const checkBtn = document.getElementById('checkBtn');
const hostInput = document.getElementById('host');
const portInput = document.getElementById('port');
const errorMsg = document.getElementById('errorMsg');
const resultCard = document.getElementById('resultCard');
const statusBadge = document.getElementById('statusBadge');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const targetLabel = document.getElementById('targetLabel');
const latencyValue = document.getElementById('latencyValue');
const timestampValue = document.getElementById('timestampValue');
const errorItem = document.getElementById('errorItem');
const errorValue = document.getElementById('errorValue');
const historyList = document.getElementById('historyList');

checkBtn.addEventListener('click', runCheck);
hostInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') runCheck(); });
portInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') runCheck(); });

async function runCheck() {
    const host = hostInput.value.trim();
    const port = parseInt(portInput.value, 10);

    hideError();

    if (!host) {
        showError('Please enter a hostname or IP address.');
        hostInput.focus();
        return;
    }
    if (!port || port < 1 || port > 65535) {
        showError('Please enter a valid port number (1-65535).');
        portInput.focus();
        return;
    }

    setLoading(true);

    try {
        const res = await fetch(`/api/check?host=${encodeURIComponent(host)}&port=${port}`);
        const data = await res.json();
        showResult(data);
        await loadHistory();
    } catch (err) {
        showError('Failed to reach the server. Is the backend running?');
    } finally {
        setLoading(false);
    }
}

function showResult(data) {
    resultCard.hidden = false;

    if (data.online) {
        statusBadge.className = 'status-badge online';
        statusDot.className = 'status-dot online';
        statusText.textContent = 'ONLINE';
        errorItem.hidden = true;
    } else {
        statusBadge.className = 'status-badge offline';
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'OFFLINE';
        errorItem.hidden = false;
        errorValue.textContent = data.error || 'Unknown error';
    }

    targetLabel.textContent = `${data.target}:${data.port}`;
    latencyValue.textContent = data.latency_ms !== null ? `${data.latency_ms} ms` : 'N/A';
    timestampValue.textContent = formatTimestamp(data.timestamp);
}

async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        const history = await res.json();
        renderHistory(history);
    } catch {
        historyList.innerHTML = '<p class="empty-state">Unable to load history.</p>';
    }
}

function renderHistory(history) {
    if (!history || history.length === 0) {
        historyList.innerHTML = '<p class="empty-state">No checks yet.</p>';
        return;
    }

    const items = [...history].reverse().map((item) => {
        const statusClass = item.online ? 'online' : 'offline';
        const statusLabel = item.online ? 'ONLINE' : 'OFFLINE';
        const latency = item.latency_ms !== null ? `${item.latency_ms} ms` : 'N/A';
        return `
            <div class="history-item">
                <span class="history-dot ${statusClass}"></span>
                <span class="history-target mono">${escapeHtml(item.target)}:${item.port}</span>
                <span class="history-status ${statusClass}">${statusLabel}</span>
                <span class="history-latency">${latency}</span>
                <span class="history-time mono">${formatTimestamp(item.timestamp)}</span>
            </div>
        `;
    }).join('');

    historyList.innerHTML = items;
}

function setLoading(loading) {
    checkBtn.disabled = loading;
    checkBtn.querySelector('.btn-text').textContent = loading ? 'Checking...' : 'Check Connection';
    checkBtn.querySelector('.btn-spinner').hidden = !loading;
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.hidden = false;
}

function hideError() {
    errorMsg.hidden = true;
}

function formatTimestamp(iso) {
    try {
        const d = new Date(iso);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
        return iso;
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

loadHistory();
