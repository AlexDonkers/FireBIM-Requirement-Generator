$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host ""
Write-Host "=== FireBIM Requirement Generator ===" -ForegroundColor Cyan
Write-Host ""

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "[1/3] Creating virtual environment..." -ForegroundColor Yellow
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    } else {
        python -m venv .venv
    }
} else {
    Write-Host "[1/3] Virtual environment already exists." -ForegroundColor Green
}

Write-Host "[2/3] Installing/updating project dependencies..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -e .

Write-Host "[3/3] Starting Streamlit..." -ForegroundColor Yellow
Write-Host ""
& $PythonExe -m streamlit run app\streamlit_app.py
