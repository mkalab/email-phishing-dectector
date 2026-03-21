REM Dừng các quy trình cũ
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul


start cmd /k "cd ai_services && python app.py"
timeout /t 5 >nul

start cmd /k "cd ai_services && python ui.py"

start cmd /k "cd web_backend && npm start"

REM Thông báo hoàn thành
echo Endpoints:
echo    - Node.js Backend: http://localhost:3000
echo    - AI Service: http://localhost:8000
echo    - Health Check: http://localhost:3000/api/health-ai
echo.
pause