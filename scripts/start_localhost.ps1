# ==============================================================================
# One-Command Localhost Startup Script for Windows PowerShell
# Reference: docs/09_DEVELOPMENT_ROADMAP_AND_AGENT_RULES.md & docs/10_TESTING_VALIDATION_DEPLOYMENT.md
# ==============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Starting MODIS-VIIRS Hotspot Harmonisation on localhost (Windows)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Environment Files Configuration
$EnvPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path $EnvPath)) {
    Write-Host "[Config] Creating root .env with localhost defaults..." -ForegroundColor Yellow
    @"
APP_ENV=development
APP_NAME="MODIS-VIIRS Hotspot Harmonisation"
DEFAULT_METHOD_VERSION=1.0.0
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_ORIGIN=http://localhost:3000
MAX_UPLOAD_SIZE_MB=50
# Uses PostgreSQL/PostGIS if running on port 5432, or local SQLite file if Docker is unavailable:
DATABASE_URL=sqlite:///./modis_viirs_local.db
FALLBACK_SQLITE_URL=sqlite:///./modis_viirs_local.db
"@ | Out-File -FilePath $EnvPath -Encoding utf8
}

$FrontendEnvPath = Join-Path $RepoRoot "frontend\.env.local"
if (-not (Test-Path $FrontendEnvPath)) {
    Write-Host "[Config] Creating frontend\.env.local..." -ForegroundColor Yellow
    if (-not (Test-Path (Join-Path $RepoRoot "frontend"))) {
        New-Item -ItemType Directory -Path (Join-Path $RepoRoot "frontend") | Out-Null
    }
    @"
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_DEFAULT_CRS=EPSG:4326
"@ | Out-File -FilePath $FrontendEnvPath -Encoding utf8
}

# 2. Local Database Detection (Docker PostGIS vs SQLite Fallback)
$dockerRunning = $false
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
} catch {
    $dockerRunning = $false
}

if ($dockerRunning) {
    Write-Host "[Database] Docker daemon detected. Starting PostgreSQL/PostGIS container..." -ForegroundColor Green
    docker compose up -d db
    Write-Host "[Database] PostgreSQL + PostGIS is ready." -ForegroundColor Green
} else {
    Write-Host "[Database] Docker daemon is not active. Using automatic local SQLite fallback." -ForegroundColor Yellow
    (Get-Content $EnvPath) -replace '^DATABASE_URL=postgresql.*', 'DATABASE_URL=sqlite:///./modis_viirs_local.db' | Set-Content $EnvPath
}

# 3. Python Virtual Environment & Dependencies
$VenvPython = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
$VenvPip = Join-Path $RepoRoot "backend\.venv\Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[Python] Initializing Python virtual environment backend\.venv..." -ForegroundColor Yellow
    python -m venv (Join-Path $RepoRoot "backend\.venv")
    & $VenvPip install --upgrade pip
    & $VenvPip install -r (Join-Path $RepoRoot "backend\requirements.txt")
}

# 4. Database Initialization & Seed Fixtures
Write-Host "[Seed] Initializing tables and seeding labelled test fixtures..." -ForegroundColor Yellow
$env:PYTHONPATH = "$RepoRoot;$RepoRoot\backend"
& $VenvPython (Join-Path $RepoRoot "scripts\seed_demo_fixtures.py")

# 5. Start FastAPI Backend Server
Write-Host "[Backend] Launching FastAPI Uvicorn on http://127.0.0.1:8000..." -ForegroundColor Green
$UvicornExe = Join-Path $RepoRoot "backend\.venv\Scripts\uvicorn.exe"
$BackendProcess = Start-Process -FilePath $UvicornExe -ArgumentList "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000" -PassThru -NoNewWindow

# Wait for FastAPI health endpoint
Write-Host "[Backend] Waiting for FastAPI health endpoint..." -ForegroundColor Yellow
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -TimeoutSec 2
        if ($resp.status -eq "ok") {
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if ($healthy) {
    Write-Host "[Backend] FastAPI is online and healthy." -ForegroundColor Green
} else {
    Write-Host "[Backend] Warning: Health check timed out, proceeding..." -ForegroundColor Yellow
}

# 6. Report Clickable Localhost URLs
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Application URLs:" -ForegroundColor Cyan
Write-Host "   - Web Frontend:              http://localhost:3000" -ForegroundColor White
Write-Host "   - FastAPI Backend API:       http://localhost:8000/api" -ForegroundColor White
Write-Host "   - Interactive Swagger Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "   - API Health Check:          http://localhost:8000/api/health" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

# 7. Start Next.js Frontend Server
Set-Location (Join-Path $RepoRoot "frontend")
if (-not (Test-Path "node_modules")) {
    npm install
}

try {
    Write-Host "[Frontend] Launching Next.js development server on http://localhost:3000..." -ForegroundColor Green
    npm run dev -- -p 3000
} finally {
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Write-Host "[Shutdown] Stopping backend process..." -ForegroundColor Yellow
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
