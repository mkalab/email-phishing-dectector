// ── Elements ───────────────────────────────────────
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

// ── Tab switching ──────────────────────────────────
document.getElementById('emailTab').addEventListener('click', () => {
    document.getElementById('emailTab').classList.add('active');
    document.getElementById('urlTab').classList.remove('active');
    document.getElementById('emailSection').classList.remove('hidden');
    document.getElementById('urlSection').classList.add('hidden');
});
document.getElementById('urlTab').addEventListener('click', () => {
    document.getElementById('urlTab').classList.add('active');
    document.getElementById('emailTab').classList.remove('active');
    document.getElementById('urlSection').classList.remove('hidden');
    document.getElementById('emailSection').classList.add('hidden');
});

// ── Reset buttons ──────────────────────────────────
document.getElementById('resetEmailBtn').addEventListener('click', resetEmailScan);
document.getElementById('resetUrlBtn').addEventListener('click', resetUrlScan);

// ── Drop zone ──────────────────────────────────────
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.style.borderColor = '#60a5fa'; });
dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = ''; });
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.style.borderColor = '';
    const file = e.dataTransfer.files[0];
    if (file) handleEmailFile(file);
});
fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) { handleEmailFile(file); fileInput.value = ''; }
});

// ── EMAIL ──────────────────────────────────────────
async function handleEmailFile(file) {
    if (!file.name.endsWith('.eml')) { alert('Vui lòng chọn file .eml'); return; }

    dropZone.classList.add('hidden');
    document.getElementById('emailLoading').classList.remove('hidden');
    document.getElementById('emailResult').classList.add('hidden');

    const formData = new FormData();
    formData.append('email_file', file);

    try {
        const res = await fetch('http://127.0.0.1:3000/api/analyze-file', { method: 'POST', body: formData });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showEmailResult(await res.json());
    } catch (err) {
        alert('❌ Không thể kết nối backend (port 3000).\nKiểm tra Node.js + Python service đang chạy.');
        resetEmailScan();
    } finally {
        document.getElementById('emailLoading').classList.add('hidden');
    }
}

function showEmailResult(data) {
    document.getElementById('emailResult').classList.remove('hidden');

    const isDangerous = data.final_verdict === 'DANGEROUS';
    const conf        = (data.email_details.ai_confidence * 100).toFixed(1);
    const suspicious  = (data.url_analysis.suspicious_urls_found || []).length;
    const total       = (data.url_analysis.urls || []).length;

    const banner = document.getElementById('emailVerdictBanner');
    banner.className = 'verdict-banner ' + (isDangerous ? 'danger' : 'safe');
    banner.innerText = isDangerous ? 'PHÁT HIỆN LỪA ĐẢO' : 'EMAIL AN TOÀN';

    const urlPart = total > 0 ? `${suspicious}/${total} link đáng ngờ` : 'Không có link';
    const summary = document.getElementById('emailSummary');
    summary.innerHTML = `Rủi ro lừa đảo: <b>${conf}%</b>&nbsp;&nbsp;|&nbsp;&nbsp;${urlPart}`;
    summary.className = 'summary-line ' + (isDangerous ? 'red-text' : 'green-text');
}

function resetEmailScan() {
    document.getElementById('emailResult').classList.add('hidden');
    document.getElementById('emailLoading').classList.add('hidden');
    dropZone.classList.remove('hidden');
    fileInput.value = '';
}

// ── URL ────────────────────────────────────────────
document.getElementById('scanUrlBtn').addEventListener('click', async () => {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) { alert('Vui lòng nhập URL'); return; }

    document.getElementById('urlInputContainer').classList.add('hidden');
    document.getElementById('urlLoading').classList.remove('hidden');
    document.getElementById('urlResult').classList.add('hidden');

    try {
        const res = await fetch('http://127.0.0.1:3000/api/analyze-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showUrlResult(await res.json());
    } catch {
        showUrlResult({ error: true });
    } finally {
        document.getElementById('urlLoading').classList.add('hidden');
    }
});

function showUrlResult(data) {
    document.getElementById('urlResult').classList.remove('hidden');

    const banner  = document.getElementById('urlVerdictBanner');
    const summary = document.getElementById('urlSummary');

    if (data.error) {
        banner.className  = 'verdict-banner warn';
        banner.innerText  = 'KHÔNG THỂ PHÂN TÍCH';
        summary.className = 'summary-line';
        summary.innerText = 'Kiểm tra backend đang chạy';
    } else if (data.is_phishing) {
        banner.className  = 'verdict-banner danger';
        banner.innerText  = 'PHÁT HIỆN LỪA ĐẢO';
        summary.className = 'summary-line red-text';
        summary.innerHTML = `Rủi ro lừa đảo: <b>${(data.confidence * 100).toFixed(1)}%</b>`;
    } else {
        banner.className  = 'verdict-banner safe';
        banner.innerText  = 'URL AN TOÀN';
        summary.className = 'summary-line green-text';
        summary.innerHTML = `Rủi ro lừa đảo: <b>${(data.confidence * 100).toFixed(1)}%</b>`;
    }
}

function resetUrlScan() {
    document.getElementById('urlResult').classList.add('hidden');
    document.getElementById('urlLoading').classList.add('hidden');
    document.getElementById('urlInputContainer').classList.remove('hidden');
    document.getElementById('urlInput').value = '';
}