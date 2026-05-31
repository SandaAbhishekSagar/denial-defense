# Denial Defense data collection runner script (PowerShell)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "===========================" -ForegroundColor Cyan
Write-Host "Denial Defense Data Collection" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""

# Check if virtual environment exists
$VenvPath = Join-Path $ProjectRoot "venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv $VenvPath
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
& $ActivateScript

# Install/upgrade dependencies
Write-Host "Installing dependencies..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r (Join-Path $ProjectRoot "requirements.txt")
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Run collection script with all phases
Write-Host "Starting data collection..."
Write-Host ""
$CollectScript = Join-Path $ScriptDir "collect_supplemental_data.py"
python $CollectScript --all --root $ProjectRoot

Write-Host ""
Write-Host "===========================" -ForegroundColor Cyan
Write-Host "Collection complete!" -ForegroundColor Green
Write-Host "Check logs/collection.log for details"
Write-Host "===========================" -ForegroundColor Cyan
