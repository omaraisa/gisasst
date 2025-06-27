# GIS Copilot Desktop Startup Script for PowerShell
Write-Host "🚀 Starting GIS Copilot Desktop..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8 or higher." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "📚 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/update requirements
Write-Host "📥 Installing/updating requirements..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install requirements" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "⚠️  Please edit .env file and add your Gemini API key!" -ForegroundColor Red
    Write-Host "Get your API key from: https://makersuite.google.com/app/apikey" -ForegroundColor Cyan
    
    $response = Read-Host "`nDo you want to open .env file now? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        notepad .env
        Write-Host "Please save the .env file and press Enter to continue..."
        Read-Host
    }
}

# Start the application
Write-Host "`n🖥️ Starting GIS Copilot Desktop..." -ForegroundColor Green
Write-Host "📖 Close the application window to stop" -ForegroundColor Yellow
Write-Host ""

python main.py
