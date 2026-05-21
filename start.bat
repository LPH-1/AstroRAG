@echo off
chcp 65001 >nul 2>&1
title AstroRAG Launcher

echo.
echo ================================================
echo   AstroRAG - Astronomy Knowledge QnA
echo ================================================
echo.

echo [1/6] Starting ChromaDB (port 8000) ...
start "ChromaDB" cmd /k "chcp 65001 >nul && title ChromaDB && chroma run --path C:\Users\34128\Projects\astronomy-rag\chroma_data"
echo        OK

echo [2/6] Starting Embedding Server (port 8081) ...
start "Embedding" cmd /k "chcp 65001 >nul && title Embedding && cd /d C:\Users\34128\Projects\astronomy-rag\data-pipeline && python embedding_server.py"
echo        OK

echo [3/6] Starting Star Chart Server (port 8082) ...
start "StarChart" cmd /k "chcp 65001 >nul && title StarChart && cd /d C:\Users\34128\Projects\astronomy-rag\data-pipeline && python starchart_server.py"
echo        OK

echo [4/6] Checking LM Studio (port 1234) ...
powershell -Command "try{$r=Invoke-RestMethod 'http://localhost:1234/v1/models' -TimeoutSec 3;Write-Host '       LM Studio is running' -ForegroundColor Green}catch{Write-Host '       WARNING: Please start LM Studio and load a chat model' -ForegroundColor Yellow}"
echo.

echo [5/6] Starting Spring Boot (port 8080) ...
if exist "C:\Users\34128\Projects\astronomy-rag\backend\mvnw.cmd" (
    start "SpringBoot" cmd /k "chcp 65001 >nul && title SpringBoot && cd /d C:\Users\34128\Projects\astronomy-rag\backend && mvnw.cmd spring-boot:run"
) else (
    start "SpringBoot" cmd /k "chcp 65001 >nul && title SpringBoot && cd /d C:\Users\34128\Projects\astronomy-rag\backend && mvn spring-boot:run"
)
echo        OK (first build may take a few minutes)

echo [6/6] Starting React Frontend (port 3000) ...
if not exist "C:\Users\34128\Projects\astronomy-rag\frontend\node_modules" (
    echo        First run: installing npm packages ...
    cd /d "C:\Users\34128\Projects\astronomy-rag\frontend"
    call npm install
    cd /d "C:\Users\34128\Projects\astronomy-rag"
)
start "React" cmd /k "chcp 65001 >nul && title React && cd /d C:\Users\34128\Projects\astronomy-rag\frontend && npm run dev"
echo        OK

echo.
echo ================================================
echo   All services started!
echo   Opening browser in 15 seconds ...
echo.
echo   Chat:    http://localhost:3000
echo   StarMap: http://localhost:8082/v1/starchart?ra=83.82^&dec=-5.39^&fov=20^&width=1200^&height=800
echo ================================================
echo.
echo Tip: close individual windows to stop services
echo.

timeout /t 15 /nobreak
start http://localhost:3000

pause
