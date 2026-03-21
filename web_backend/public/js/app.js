document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');

    // =============================================
    // TAB SWITCHING
    // =============================================
    document.getElementById('emailTab').addEventListener('click', () => switchTab('email'));
    document.getElementById('urlTab').addEventListener('click', () => switchTab('url'));

    function switchTab(tab) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active', 'bg-blue-600', 'bg-emerald-600');
            btn.classList.add('bg-gray-600');
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        if (tab === 'email') {
            document.getElementById('emailTab').classList.add('active', 'bg-blue-600');
            document.getElementById('emailTab').classList.remove('bg-gray-600');
            document.getElementById('emailSection').classList.remove('hidden');
        } else {
            document.getElementById('urlTab').classList.add('active', 'bg-emerald-600');
            document.getElementById('urlTab').classList.remove('bg-gray-600');
            document.getElementById('urlSection').classList.remove('hidden');
        }
    }

    // =============================================
    // EMAIL - DRAG & DROP
    // =============================================
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        handleEmailFile(files[0]);
    });

    fileInput.onchange = () => {
        handleEmailFile(fileInput.files[0]);
    };

    // =============================================
    // EMAIL - XỬ LÝ FILE
    // =============================================
    async function handleEmailFile(file) {
        if (!file || !file.name.endsWith('.eml')) {
            alert('Vui lòng tải lên file định dạng .eml');
            return;
        }

        document.getElementById('uploadContainer').classList.add('hidden');
        document.getElementById('emailResult').classList.add('hidden');
        document.getElementById('emailLoading').classList.remove('hidden');

        const formData = new FormData();
        formData.append('email_file', file);

        try {
            const res = await fetch('/api/analyze-file', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || 'Server error');
            }

            const data = await res.json();
            showEmailResult(data);
        } catch (error) {
            console.error('Error:', error);
            alert('Có lỗi xảy ra khi phân tích email!');
            resetEmailScan();
        }
    }

    // =============================================
    // EMAIL - HIỂN THỊ KẾT QUẢ
    // =============================================
    function showEmailResult(data) {
        document.getElementById('emailLoading').classList.add('hidden');
        document.getElementById('emailResult').classList.remove('hidden');

        const banner = document.getElementById('emailVerdictBanner');
        const aiConf = document.getElementById('emailAiConf');
        const emailVerdict = document.getElementById('emailVerdict');
        const emailContentDetails = document.getElementById('emailContentDetails');

        // --- Verdict banner ---
        if (data.final_verdict === 'DANGEROUS') {
            banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-red-500/20 text-red-400 border border-red-500/50 animate__animated animate__headShake';
            banner.innerText = 'PHÁT HIỆN LỪA ĐẢO';
            emailVerdict.innerText = 'Lừa đảo';
            emailVerdict.className = 'text-2xl font-mono text-red-400';
        } else {
            banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 animate__animated animate__fadeIn';
            banner.innerText = 'EMAIL AN TOÀN';
            emailVerdict.innerText = 'An toàn';
            emailVerdict.className = 'text-2xl font-mono text-emerald-400';
        }

        // --- AI confidence ---
        aiConf.innerText = (data.analysis.ai_confidence * 100).toFixed(1) + '%';



        // =============================================
        // URL SECTION - tổng / an toàn / đáng ngờ
        // =============================================
        const suspiciousUrls = data.analysis.suspicious_urls_found || [];
        const allUrls = data.analysis.all_urls_found || [];

        // Lấy danh sách URL an toàn = tất cả URLs trừ URL đáng ngờ
        const suspiciousSet = new Set(suspiciousUrls.map(u => u.url));
        const safeUrls = allUrls.filter(url => !suspiciousSet.has(url));

        const totalCount = allUrls.length > 0
            ? allUrls.length
            : (data.analysis.total_urls_found ?? suspiciousUrls.length);

        // Cập nhật số liệu thống kê
        document.getElementById('urlTotalCount').innerText = totalCount;
        document.getElementById('urlSafeCount').innerText = safeUrls.length;
        document.getElementById('urlThreatCount').innerText = suspiciousUrls.length;

        // Màu sắc cho số đáng ngờ
        document.getElementById('urlThreatCount').className =
            suspiciousUrls.length > 0
                ? 'text-xl font-mono font-bold text-red-400'
                : 'text-xl font-mono font-bold text-emerald-400';

        // --- Danh sách URL AN TOÀN ---
        const safeUrlsList = document.getElementById('safeUrlsList');
        safeUrlsList.innerHTML = '';
        if (safeUrls.length === 0) {
            const li = document.createElement('li');
            li.className = 'text-gray-500 italic text-sm';
            li.innerText = 'Không có URL an toàn';
            safeUrlsList.appendChild(li);
        } else {
            safeUrls.forEach(url => {
                const li = document.createElement('li');
                li.className = 'flex items-start gap-2 text-emerald-300 bg-emerald-500/10 rounded-xl px-4 py-2 border border-emerald-500/20';
                li.innerHTML = `
                    <span class="shrink-0 mt-0.5"></span>
                    <span class="font-mono text-sm break-all">${url}</span>`;
                safeUrlsList.appendChild(li);
            });
        }

        // --- Danh sách URL ĐÁNG NGỜ ---
        const suspiciousUrlsList = document.getElementById('suspiciousUrlsList');
        suspiciousUrlsList.innerHTML = '';
        if (suspiciousUrls.length === 0) {
            const li = document.createElement('li');
            li.className = 'text-gray-500 italic text-sm';
            li.innerText = 'Không phát hiện URL đáng ngờ';
            suspiciousUrlsList.appendChild(li);
        } else {
            suspiciousUrls.forEach(urlInfo => {
                const li = document.createElement('li');
                li.className = 'flex items-start gap-2 text-red-300 bg-red-500/10 rounded-xl px-4 py-2 border border-red-500/20';
                li.innerHTML = `
                    <span class="shrink-0 mt-0.5">⚠️</span>
                    <span>
                        <span class="font-mono text-sm break-all">${urlInfo.url}</span>
                        <span class="text-red-400/70 text-xs ml-2">(${(urlInfo.confidence * 100).toFixed(1)}%)</span>
                    </span>`;
                suspiciousUrlsList.appendChild(li);
            });
        }
    }

    // =============================================
    // URL SCANNING
    // =============================================
    document.getElementById('scanUrlBtn').addEventListener('click', async () => {
        const urlInput = document.getElementById('urlInput');
        const url = urlInput.value.trim();

        if (!url) {
            alert('Vui lòng nhập URL');
            return;
        }

        document.getElementById('urlInputContainer').classList.add('hidden');
        document.getElementById('urlResult').classList.add('hidden');
        document.getElementById('urlLoading').classList.remove('hidden');

        try {
            const response = await fetch('/api/analyze-url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                throw new Error('Server error');
            }

            const data = await response.json();
            showUrlResult(data);
        } catch (error) {
            console.error('URL Scan Error:', error);
            // Hiển thị kết quả lỗi đơn giản
            showUrlResult({ is_phishing: null, error: true });
        }
    });

    function showUrlResult(data) {
        document.getElementById('urlLoading').classList.add('hidden');
        document.getElementById('urlResult').classList.remove('hidden');

        const banner = document.getElementById('urlVerdictBanner');

        if (data.error) {
            banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/50 animate__animated animate__fadeIn';
            banner.innerText = '⚠️ KHÔNG THỂ PHÂN TÍCH';
        } else if (data.is_phishing) {
            banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-red-500/20 text-red-400 border border-red-500/50 animate__animated animate__headShake';
            banner.innerText = '⚠️ PHÁT HIỆN LỪA ĐẢO';
        } else {
            banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 animate__animated animate__fadeIn';
            banner.innerText = 'URL AN TOÀN';
        }
    }
});

// =============================================
// RESET FUNCTIONS (gọi từ HTML onclick)
// =============================================
function resetEmailScan() {
    document.getElementById('emailResult').classList.add('hidden');
    document.getElementById('emailLoading').classList.add('hidden');
    document.getElementById('uploadContainer').classList.remove('hidden');
    document.getElementById('fileInput').value = '';
}

function resetUrlScan() {
    document.getElementById('urlResult').classList.add('hidden');
    document.getElementById('urlLoading').classList.add('hidden');
    document.getElementById('urlInputContainer').classList.remove('hidden');
    document.getElementById('urlInput').value = '';
}