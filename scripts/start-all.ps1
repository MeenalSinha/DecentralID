<#
.SYNOPSIS
    Starts the complete DecentralID development stack (Hardhat, Backend, Frontend).
.DESCRIPTION
    DecentralID Local Development Orchestrator for Windows PowerShell.
    Spins up:
      1. Local Hardhat Blockchain Node (http://127.0.0.1:8545)
      2. Smart Contract Registry Deployment
      3. SQLite Database Migrations (Alembic)
      4. FastAPI Backend API Gateway (http://127.0.0.1:8000)
      5. Vite Frontend React Dashboard (http://127.0.0.1:5173)
#>

$ErrorActionPreference = "Stop"
$rootDir = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $rootDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         DecentralID - Complete Stack Startup            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Hardhat Node
$hardhatPort = 8545
$hardhatConn = Test-NetConnection -ComputerName 127.0.0.1 -Port $hardhatPort -WarningAction SilentlyContinue
if (-not $hardhatConn.TcpTestSucceeded) {
    Write-Host "[1/5] Starting Hardhat blockchain node on port 8545..." -ForegroundColor Yellow
    Start-Process -FilePath "npx.cmd" -ArgumentList "hardhat node" -WorkingDirectory $rootDir -WindowStyle Minimized
    Start-Sleep -Seconds 4
} else {
    Write-Host "[1/5] Hardhat node already running on port 8545." -ForegroundColor Green
}

# 2. Deploy Registries if needed
$manifestPath = Join-Path $rootDir "deployments\localhost\manifest.json"
if (-not (Test-Path $manifestPath)) {
    Write-Host "[2/5] Deploying smart contracts to localhost..." -ForegroundColor Yellow
    & npx.cmd hardhat run scripts/deploy/deploy_registries.js --network localhost
} else {
    Write-Host "[2/5] Contract deployments detected in deployments/localhost/manifest.json." -ForegroundColor Green
}

# 3. Database Migrations
Write-Host "[3/5] Verifying database migrations..." -ForegroundColor Yellow
$pyPath = Join-Path $rootDir "backend\venv\Scripts\python.exe"
if (-not (Test-Path $pyPath)) {
    $pyPath = "python"
}
Push-Location (Join-Path $rootDir "backend")
& $pyPath -m alembic upgrade head
Pop-Location

# Ensure root decentralid.db is synchronized
if (Test-Path (Join-Path $rootDir "backend\decentralid.db")) {
    Copy-Item (Join-Path $rootDir "backend\decentralid.db") (Join-Path $rootDir "decentralid.db") -Force
}

# 4. FastAPI Backend
$backendPort = 8000
$backendConn = Test-NetConnection -ComputerName 127.0.0.1 -Port $backendPort -WarningAction SilentlyContinue
if (-not $backendConn.TcpTestSucceeded) {
    Write-Host "[4/5] Starting FastAPI backend on port 8000..." -ForegroundColor Yellow
    Start-Process -FilePath $pyPath -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $rootDir -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[4/5] Backend already running on port 8000." -ForegroundColor Green
}

# 5. Vite Frontend
$frontendPort = 5173
$frontendConn = Test-NetConnection -ComputerName 127.0.0.1 -Port $frontendPort -WarningAction SilentlyContinue
if (-not $frontendConn.TcpTestSucceeded) {
    Write-Host "[5/5] Starting Vite frontend on port 5173..." -ForegroundColor Yellow
    Start-Process -FilePath "npm.cmd" -ArgumentList "run dev -- --host 127.0.0.1" -WorkingDirectory (Join-Path $rootDir "frontend") -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[5/5] Frontend already running on port 5173." -ForegroundColor Green
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "         DecentralID Services Status: ACTIVE              " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Frontend Dashboard:     http://localhost:5173"
Write-Host "Backend API Base:       http://localhost:8000"
Write-Host "Swagger Documentation:  http://localhost:8000/docs"
Write-Host "OpenAPI Specification:  http://localhost:8000/api/v1/openapi.json"
Write-Host "Blockchain RPC Node:    http://127.0.0.1:8545 (Chain ID: 31337)"
Write-Host "Health Probe:           http://localhost:8000/api/v1/health/ready"
Write-Host "==========================================================`n" -ForegroundColor Green
