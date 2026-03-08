document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const uploadContainer = document.getElementById('uploadContainer');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');

    // Xử lý sự kiện kéo thả (Drag & Drop)
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files[0]);
    });

    // Xử lý khi chọn file qua nút bấm
    fileInput.onchange = () => {
        handleFiles(fileInput.files[0]);
    };

    async function handleFiles(file) {
        if (!file || !file.name.endsWith('.eml')) {
            alert('Vui lòng tải lên file định dạng .eml');
            return;
        }

        // Hiển thị trạng thái Loading
        uploadContainer.classList.add('hidden');
        loading.classList.remove('hidden');

        const formData = new FormData();
        formData.append('email_file', file);

        try {
            // Gọi đến Backend Node.js
            const res = await fetch('/api/analyze-file', { 
                method: 'POST', 
                body: formData 
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || 'Server error');
            }

            const data = await res.json();
            showResult(data);
        } catch (error) {
            console.error('Error:', error);
            alert('Có lỗi xảy ra khi phân tích email!');
            location.reload();
        }
    }

    function showResult(data) {
        loading.classList.add('hidden');
        result.classList.remove('hidden');
        
        const banner = document.getElementById('verdictBanner');
        const aiConf = document.getElementById('aiConf');
        const urlThreat = document.getElementById('urlThreat');
        const aiLabel = aiConf.previousElementSibling;
        const threatLabel = urlThreat.previousElementSibling;

        // Cập nhật Labels cho email scanning
        aiLabel.innerText = 'Độ tin cậy AI';
        threatLabel.innerText = 'Mối đe dọa URL';

        // Cập nhật Banner kết quả
        if (data.final_verdict === 'DANGEROUS') {
            banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-red-500/20 text-red-400 border border-red-500/50 animate__animated animate__headShake';
            banner.innerText = '⚠️ PHÁT HIỆN LỪA ĐẢO';
        } else {
            banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 animate__animated animate__fadeIn';
            banner.innerText = '✅ EMAIL AN TOÀN';
        }

        // Cập nhật con số thống kê
        aiConf.innerText = (data.analysis.ai_confidence * 100).toFixed(1) + '%';
        aiConf.className = 'text-3xl font-mono text-blue-400';
        
        const threatCount = data.analysis.suspicious_urls_found ? data.analysis.suspicious_urls_found.length : 0;
        urlThreat.innerText = threatCount;
        urlThreat.className = 'text-3xl font-mono text-emerald-400';
    }
});

// URL Scanning
document.getElementById('scanUrlBtn').addEventListener('click', async () => {
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    
    if (!url) {
        alert('Vui lòng nhập URL');
        return;
    }

    // Hiển thị trạng thái Loading
    uploadContainer.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const response = await fetch('/api/analyze-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Server error');
        }

        const data = await response.json();
        showUrlResult(data, url);
    } catch (error) {
        console.error('URL Scan Error:', error);
        alert('Có lỗi xảy ra khi phân tích URL!');
        location.reload();
    }
});

function showUrlResult(data, url) {
    uploadContainer.classList.add('hidden');
    loading.classList.add('hidden');
    result.classList.remove('hidden');
    
    const banner = document.getElementById('verdictBanner');
    const aiConf = document.getElementById('aiConf');
    const urlThreat = document.getElementById('urlThreat');
    const aiLabel = aiConf.previousElementSibling;
    const threatLabel = urlThreat.previousElementSibling;

    // Cập nhật Banner kết quả
    if (data.is_phishing) {
        banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-red-500/20 text-red-400 border border-red-500/50 animate__animated animate__headShake';
        banner.innerText = '⚠️ PHÁT HIỆN LỪA ĐẢO';
    } else {
        banner.className = 'rounded-2xl p-6 mb-8 text-center text-2xl font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 animate__animated animate__fadeIn';
        banner.innerText = '✅ URL AN TOÀN';
    }

    // Cập nhật labels cho URL scanning
    aiLabel.innerText = 'Phương thức phát hiện';
    threatLabel.innerText = 'Trạng thái';

    // Cập nhật con số
    aiConf.innerText = data.method_used;
    aiConf.className = 'text-2xl font-mono text-blue-400';
    
    urlThreat.innerText = data.is_phishing ? '⚠️ Lừa đảo' : '✓ An toàn';
    urlThreat.className = `text-2xl font-mono ${data.is_phishing ? 'text-red-400' : 'text-emerald-400'}`;
}