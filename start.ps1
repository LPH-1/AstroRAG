# AstroRAG one-click startup script
# Run from the project root: .\start.ps1
param(
    [switch]$SkipChroma,
    [switch]$SkipEmbedding,
    [switch]$SkipStarChart,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$projectRoot = "C:\Users\34128\Projects\astronomy-rag"

function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command
    )

    Start-Process powershell @(
        "-NoExit",
        "-Command",
        "Write-Host '$Title' -ForegroundColor Cyan; $Command"
    )
}

Write-Host "`nAstroRAG startup" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor DarkGray

$chromaAvailable = Get-Command chroma -ErrorAction SilentlyContinue
$pythonAvailable = Get-Command python -ErrorAction SilentlyContinue

if (-not $pythonAvailable) {
    Write-Host "Error: python was not found in PATH." -ForegroundColor Red
    Write-Host "Install Python or add it to PATH before running this script." -ForegroundColor Gray
    exit 1
}

if (-not $SkipChroma) {
    Write-Host "`n[1/6] ChromaDB on port 8000 ..." -ForegroundColor Yellow
    if ($chromaAvailable) {
        Start-ServiceWindow "ChromaDB starting..." "chroma run --path `"$projectRoot\chroma_data`""
    } else {
        Start-ServiceWindow "ChromaDB starting..." "python -m chromadb.cli.cli run --path `"$projectRoot\chroma_data`""
    }
    Write-Host "        Started" -ForegroundColor Green
} else {
    Write-Host "`n[1/6] ChromaDB skipped" -ForegroundColor DarkGray
}

if (-not $SkipEmbedding) {
    Write-Host "[2/6] Embedding server on port 8081 ..." -ForegroundColor Yellow
    Start-ServiceWindow "Embedding server starting..." "`$env:HF_ENDPOINT = 'https://hf-mirror.com'; cd `"$projectRoot\data-pipeline`"; python embedding_server.py"
    Write-Host "        Started" -ForegroundColor Green
} else {
    Write-Host "[2/6] Embedding server skipped" -ForegroundColor DarkGray
}

if (-not $SkipStarChart) {
    Write-Host "[3/6] Star Chart server on port 8082 ..." -ForegroundColor Yellow
    Start-ServiceWindow "Star Chart server starting..." "cd `"$projectRoot\data-pipeline`"; python starchart_server.py"
    Write-Host "        Started" -ForegroundColor Green
} else {
    Write-Host "[3/6] Star Chart server skipped" -ForegroundColor DarkGray
}

Write-Host "[4/6] LM Studio on port 1234 ..." -ForegroundColor Yellow
$lmRunning = $false
try {
    $r = Invoke-RestMethod -Uri "http://localhost:1234/v1/models" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($r.data) {
        $models = ($r.data | ForEach-Object { $_.id }) -join ", "
        Write-Host "        LM Studio detected" -ForegroundColor Green
        Write-Host "        Loaded models: $models" -ForegroundColor Gray
        $lmRunning = $true
    }
} catch {}

if (-not $lmRunning) {
    Write-Host "        Please start LM Studio manually:" -ForegroundColor Magenta
    Write-Host "          1. Open LM Studio" -ForegroundColor Gray
    Write-Host "          2. Load Qwen2.5-7B-Instruct or another local model" -ForegroundColor Gray
    Write-Host "          3. Developer -> Start Server on port 1234" -ForegroundColor Gray
}

if (-not $SkipBackend) {
    Write-Host "[5/6] Spring Boot backend on port 8080 ..." -ForegroundColor Yellow
    $mvnCmd = if (Test-Path "$projectRoot\backend\mvnw.cmd") {
        ".\mvnw.cmd"
    } elseif (Test-Path "$projectRoot\backend\mvnw") {
        ".\mvnw"
    } else {
        "mvn"
    }

    Start-ServiceWindow "Spring Boot starting..." "cd `"$projectRoot\backend`"; $mvnCmd spring-boot:run"
    Write-Host "        Started" -ForegroundColor Green
} else {
    Write-Host "[5/6] Spring Boot backend skipped" -ForegroundColor DarkGray
}

if (-not $SkipFrontend) {
    Write-Host "[6/6] React frontend on port 3000 ..." -ForegroundColor Yellow
    if (-not (Test-Path "$projectRoot\frontend\node_modules")) {
        Write-Host "        Installing frontend dependencies..." -ForegroundColor Gray
        Push-Location "$projectRoot\frontend"
        npm install
        Pop-Location
    }

    Start-ServiceWindow "React frontend starting..." "cd `"$projectRoot\frontend`"; npm.cmd run dev -- --host 127.0.0.1"
    Write-Host "        Started" -ForegroundColor Green
} else {
    Write-Host "[6/6] React frontend skipped" -ForegroundColor DarkGray
}

if (-not $NoBrowser) {
    Write-Host "`nOpening browser after services warm up..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
    Start-Process "http://localhost:3000"
}

Write-Host "`nAll startup commands were dispatched." -ForegroundColor Green
Write-Host "Open http://localhost:3000" -ForegroundColor Green
Write-Host "Close each service window to stop it.`n" -ForegroundColor Gray
