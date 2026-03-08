const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const cors = require('cors');

const app = express();
const path = require('path');

// Cấu hình CORS để Extension có thể gọi API
app.use(cors()); 
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const upload = multer({ storage: multer.memoryStorage() });

const AI_SERVICE_URL = 'http://127.0.0.1:8000';
const PORT = 3000;

// Root endpoint
app.get('/', (req, res) => {
    res.json({ 
        status: 'OK', 
        message: 'Email Phishing Detection Backend',
        endpoints: {
            health: 'GET /health',
            healthAI: 'GET /api/health-ai',
            analyzeText: 'POST /api/analyze-text',
            analyzeFile: 'POST /api/analyze-file'
        }
    });
});

// Health check endpoint - kiểm tra server có chạy không
app.get('/health', (req, res) => {
    res.json({ status: 'OK', message: 'Node.js Backend đang chạy' });
});

// Health check AI Service
app.get('/api/health-ai', async (req, res) => {
    try {
        const response = await axios.get(`${AI_SERVICE_URL}/health`, { timeout: 5000 });
        res.json({ status: 'OK', message: 'AI Service đang chạy', details: response.data });
    } catch (error) {
        res.status(503).json({ 
            status: 'ERROR', 
            message: 'Không thể kết nối với AI Service (Python)',
            details: 'Hãy chạy: python ai_services/app.py'
        });
    }
});

// 1. Quét nội dung văn bản (Dùng cho Popup/Gmail)
app.post('/api/analyze-text', async (req, res) => {
    try {
        const { subject, content } = req.body;
        
        if (!subject && !content) {
            return res.status(400).json({ error: 'Vui lòng cung cấp subject hoặc content' });
        }

        const response = await axios.post(`${AI_SERVICE_URL}/predict`, {
            subject: subject || "",
            content: content || ""
        }, { timeout: 30000 });
        
        res.json(response.data);
    } catch (error) {
        console.error("AI Service Error:", error.message);
        
        if (error.code === 'ECONNREFUSED') {
            return res.status(503).json({ 
                error: 'Không thể kết nối với AI Service',
                message: 'Hãy chạy Python service: python ai_services/app.py trên port 8000'
            });
        }
        
        res.status(500).json({ 
            error: 'Lỗi phân tích văn bản',
            details: error.message 
        });
    }
});

// 2. Quét file .eml (Dùng cho kéo thả file vào Popup)
app.post('/api/analyze-file', upload.single('email_file'), async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ error: 'Không có file' });
        
        const form = new FormData();
        form.append('file', req.file.buffer, { filename: req.file.originalname });

        const response = await axios.post(`${AI_SERVICE_URL}/predict-eml`, form, {
            headers: { ...form.getHeaders() },
            timeout: 30000
        });
        
        res.json(response.data);
    } catch (error) {
        console.error("File Analysis Error:", error.message);
        
        if (error.code === 'ECONNREFUSED') {
            return res.status(503).json({ 
                error: 'Không thể kết nối với AI Service',
                message: 'Hãy chạy Python service: python ai_services/app.py trên port 8000'
            });
        }
        
        res.status(500).json({ error: 'Lỗi xử lý file AI', details: error.message });
    }
});

// 3. Quét URL đơn lẻ
app.post('/api/analyze-url', async (req, res) => {
    try {
        const { url } = req.body;
        
        if (!url) {
            return res.status(400).json({ error: 'Vui lòng cung cấp URL' });
        }

        const response = await axios.post(`${AI_SERVICE_URL}/predict-url`, {
            url: url
        }, { timeout: 10000 });
        
        res.json(response.data);
    } catch (error) {
        console.error("URL Analysis Error:", error.message);
        
        if (error.code === 'ECONNREFUSED') {
            return res.status(503).json({ 
                error: 'Không thể kết nối với AI Service',
                message: 'Hãy chạy Python service: python ai_services/app.py trên port 8000'
            });
        }
        
        res.status(500).json({ 
            error: 'Lỗi phân tích URL',
            details: error.message 
        });
    }
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Endpoint không tồn tại' });
});

// Error handler
app.use((err, req, res, next) => {
    console.error('Server Error:', err);
    res.status(500).json({ error: 'Lỗi server nội bộ', details: err.message });
});

// Khởi động server
const server = app.listen(PORT, '127.0.0.1', () => {
    console.log(`\nNode.js Backend started successfully!`);
    console.log(`Server running at http://localhost:${PORT}`);
    console.log(`API Documentation: http://localhost:${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
    console.log(`\nMake sure AI Service is running on port 8000`);
    console.log(`Run: python ai_services/app.py\n`);
});


// Xử lý lỗi server
server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
        console.error(`Port ${PORT} đã được sử dụng. Vui lòng đóng ứng dụng khác hoặc thay đổi PORT.`);
    } else {
        console.error('Server Error:', error);
    }
    process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('Đang tắt server...');
    server.close(() => {
        console.log('Server đã tắt');
        process.exit(0);
    });
});