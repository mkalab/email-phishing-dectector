@echo off
REM Email Phishing Detection - Project Launcher
echo ============================================
echo  🛡️  Email Phishing Detection Project
echo ============================================

REM Check if models exist
if not exist "ai_services\phishing_classifier_final\config.json" (
    echo ⚠️  AI Models not found!
    echo.
    echo Setting up models...
    python setup_models.py --all --mock
    echo.
)

REM Dừng các quy trình cũ
echo 🛑 Stopping existing processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

echo.
echo 🚀 Starting services...

start "AI Service" cmd /k "cd ai_services && echo Starting AI Service... && python app.py"
timeout /t 5 >nul

start "Test UI" cmd /k "cd ai_services && echo Starting Test UI... && python ui.py"

start "Node.js Backend" cmd /k "cd web_backend && echo Starting Node.js Backend... && npm start"

REM Thông báo hoàn thành
echo.
echo ============================================
echo ✅ All services started successfully!
echo.
echo 🌐 Available endpoints:
echo    - Node.js Backend: http://localhost:3000
echo    - AI Service: http://localhost:8000
echo    - Test UI: http://localhost:8100
echo    - Health Check: http://localhost:3000/api/health-ai
echo.
echo 📝 To stop all services, close the command windows
echo ============================================
pause