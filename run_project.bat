@echo off
REM ========================================
REM Email Phishing Detection System
REM ========================================
echo.
echo ╔════════════════════════════════════════╗
echo ║  🛡️  Email Phishing Detection System   ║
echo ╚════════════════════════════════════════╝
echo.

REM Dừng các quy trình cũ
echo 🔄 Dừng các quy trình cũ...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

REM Khởi động AI Service (Python)
echo.
echo 📚 Khởi động AI Service (Python)...
echo.
start cmd /k "cd ai_services && python app.py"

REM Chờ AI Service khởi động
timeout /t 5 >nul

start cmd /k "cd ai_services && python ui.py"


REM Khởi động Node.js Backend
echo.
echo 🚀 Khởi động Node.js Backend...
echo.
start cmd /k "cd web_backend && npm start"

REM Thông báo hoàn thành
echo.
echo ✅ Tất cả services đã được khởi động!
echo.
echo 📌 Endpoints:
echo    - Node.js Backend: http://localhost:3000
echo    - AI Service: http://localhost:8000
echo    - Health Check: http://localhost:3000/api/health-ai
echo.
pause