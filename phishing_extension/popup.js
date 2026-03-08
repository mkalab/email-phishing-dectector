const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const emailTab = document.getElementById('emailTab');
const urlTab = document.getElementById('urlTab');
const emailSection = document.getElementById('emailSection');
const urlSection = document.getElementById('urlSection');
const urlInput = document.getElementById('urlInput');
const scanUrlBtn = document.getElementById('scanUrlBtn');

// Tab switching
emailTab.addEventListener('click', () => {
    emailTab.classList.add('active');
    urlTab.classList.remove('active');
    emailSection.classList.remove('hidden');
    urlSection.classList.add('hidden');
    resetUI();
});

urlTab.addEventListener('click', () => {
    urlTab.classList.add('active');
    emailTab.classList.remove('active');
    urlSection.classList.remove('hidden');
    emailSection.classList.add('hidden');
    resetUI();
});

// URL scanning
scanUrlBtn.addEventListener('click', () => {
    const url = urlInput.value.trim();
    if (!url) {
        alert('Vui lòng nhập URL');
        return;
    }
    handleUrlScan(url);
});

// Sửa lỗi nhảy 2 lần: Chỉ gọi click() khi thực sự nhấn vào vùng DropZone
dropZone.addEventListener('click', (e) => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleUpload(file);
        // Reset giá trị để có thể chọn lại cùng 1 file nếu cần
        fileInput.value = ''; 
    }
});

async function handleUpload(file) {
    const loading = document.getElementById('loading');
    const resultArea = document.getElementById('resultArea');
    
    loading.classList.remove('hidden');
    resultArea.classList.add('hidden');

    const formData = new FormData();
    formData.append('email_file', file);

    try {
        const response = await fetch('http://127.0.0.1:3000/api/analyze-file', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorData}`);
        }
        const data = await response.json();
        showSimpleUI(data);
    } catch (err) {
        console.error("Extension error:", err);
        alert(`❌ Lỗi kết nối Backend tại 127.0.0.1:3000\n\nGiải pháp:\n1. Kiểm tra Node.js backend chạy: npm start\n2. Kiểm tra port 3000 có khả dụng\n3. Kiểm tra Python AI service chạy\n\nChi tiết: ${err.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

function showSimpleUI(data) {
    const resultArea = document.getElementById('resultArea');
    const contentRes = document.getElementById('contentRes');
    const urlRes = document.getElementById('urlRes');
    
    resultArea.classList.remove('hidden');

    const conf = (data.analysis.ai_confidence * 100).toFixed(0);
    const isDangerous = data.final_verdict === 'DANGEROUS';

    contentRes.innerHTML = `Nội dung: <span class="${isDangerous ? 'red' : 'green'}">${isDangerous ? 'Lừa đảo' : 'An toàn'} (${conf}%)</span>`;

    // Fix: API trả về suspicious_urls_found (array) và urls_extracted (array)
    const threatCount = data.analysis.suspicious_urls_found ? data.analysis.suspicious_urls_found.length : 0;
    const totalUrls = data.analysis.urls_extracted ? data.analysis.urls_extracted.length : 0;
    urlRes.innerHTML = `Liên kết: <span class="${threatCount > 0 ? 'red' : ''}">${totalUrls > 0 ? `Phát hiện ${threatCount}/${totalUrls} link nghi vấn` : 'Không phát hiện link'}</span>`;
}

// Reset UI khi chuyển tab
function resetUI() {
    const loading = document.getElementById('loading');
    const resultArea = document.getElementById('resultArea');
    loading.classList.add('hidden');
    resultArea.classList.add('hidden');
}

// URL Scan Handler
async function handleUrlScan(url) {
    const loading = document.getElementById('loading');
    const resultArea = document.getElementById('resultArea');
    
    loading.classList.remove('hidden');
    resultArea.classList.add('hidden');

    try {
        const response = await fetch('http://127.0.0.1:3000/api/analyze-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorData}`);
        }
        const data = await response.json();
        showUrlResult(data, url);
    } catch (err) {
        console.error("URL Scan error:", err);
        alert(`❌ Lỗi kết nối Backend tại 127.0.0.1:3000\n\nGiải pháp:\n1. Kiểm tra Node.js backend chạy: npm start\n2. Kiểm tra port 3000 có khả dụng\n3. Kiểm tra Python AI service chạy\n\nChi tiết: ${err.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

// Show URL Result
function showUrlResult(data, url) {
    const resultArea = document.getElementById('resultArea');
    const contentRes = document.getElementById('contentRes');
    const urlRes = document.getElementById('urlRes');
    
    resultArea.classList.remove('hidden');

    const isDangerous = data.is_phishing;
    const method = data.method_used;

    contentRes.innerHTML = `URL: <a href="${url}" target="_blank" class="url-link" style="color: #60a5fa; text-decoration: none;">${url}</a>`;
    urlRes.innerHTML = `Kết quả: <span class="${isDangerous ? 'red' : 'green'}" style="font-weight: bold;">${isDangerous ? '⚠️ Lừa đảo' : '✅ An toàn'} (${method})</span>`;
}