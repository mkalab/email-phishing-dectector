// Hàm tìm vị trí và chèn nút
function injectScanButton() {
    // Thử nhiều selector khác nhau vì Gmail UI có thể thay đổi
    const possibleSelectors = [
        '.gE.iv.gt',  // Cũ
        '.gE',        // Chung hơn
        '[role="button"]', // Nút chung
        '.T-I',       // Nút Gmail
        '.brq'        // Khu vực header
    ];

    let targetElement = null;
    for (const selector of possibleSelectors) {
        const elements = document.querySelectorAll(selector);
        for (const el of elements) {
            // Kiểm tra nếu element có text liên quan đến email actions
            if (el.textContent && (el.textContent.includes('Reply') || el.textContent.includes('Forward') || el.closest('.adn'))) {
                targetElement = el;
                break;
            }
        }
        if (targetElement) break;
    }

    // Nếu không tìm thấy, thử tìm khu vực header email
    if (!targetElement) {
        targetElement = document.querySelector('.adn.adH') || document.querySelector('.ha') || document.querySelector('.hP').parentElement;
    }

    if (!targetElement) {
        console.log('Gmail UI changed - cannot find injection point for scan button');
        return;
    }

    // Kiểm tra đã có nút chưa
    if (targetElement.querySelector('.ai-scan-wrapper')) return;

    // Tạo container cho nút
    const btnWrapper = document.createElement('div');
    btnWrapper.className = 'ai-scan-wrapper';
    btnWrapper.style.display = 'inline-block';
    btnWrapper.style.marginLeft = '15px';
    btnWrapper.style.verticalAlign = 'middle';

    btnWrapper.innerHTML = `
        <button class="ai-scan-btn" style="
            background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            font-size: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.2s;
        ">
            🛡️ Scan with AI
        </button>
    `;

    btnWrapper.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        performScan(targetElement);
    };

    targetElement.appendChild(btnWrapper);
    console.log('Scan button injected successfully');
}

// Hàm lấy dữ liệu
async function performScan(element) {
    try {
        // Tìm nội dung email gần nhất với vị trí nút bấm
        const container = element.closest('.btV') || document;
        const bodyText = container.querySelector('.a3s.aiL')?.innerText || "No content found";
        const subjectText = document.querySelector('.hP')?.innerText || "No subject";

        console.log("Scanning Subject:", subjectText);

        // Hiển thị thông báo đang xử lý
        const btn = element.querySelector('.ai-scan-btn');
        const originalText = btn.innerText;
        btn.innerText = "⏳ Scanning...";
        btn.disabled = true;

        const response = await fetch('http://localhost:3000/api/analyze-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject: subjectText, content: bodyText })
        });
        
        const data = await response.json();
        
        // Hiển thị kết quả bằng Alert hoặc UI tùy chọn
        if (data.final_verdict === 'DANGEROUS') {
            alert(`CẢNH BÁO NGUY HIỂM!\nAI đánh giá lừa đảo: ${(data.analysis.ai_confidence * 100).toFixed(1)}%`);
        } else {
            alert(`AN TOÀN\nĐộ tin cậy: ${(data.analysis.ai_confidence * 100).toFixed(1)}%`);
        }

        btn.innerText = originalText;
        btn.disabled = false;

    } catch (err) {
        console.error(err);
        alert("❌ Lỗi: Backend Node.js tại port 3000 không khả dụng\n\nGiải pháp:\n1. Chạy: cd web_backend && npm start\n2. Đảm bảo Python AI service chạy (port 8000)\n3. Reload lại extension nếu cần\n\nChi tiết: " + err.message);
    }
}

// Chạy kiểm tra mỗi giây để bám sát việc Gmail load email mới
setInterval(injectScanButton, 1500);