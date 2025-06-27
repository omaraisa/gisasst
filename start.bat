@echo off
echo 🚀 Starting GIS Copilot Desktop...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 📚 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements
echo 📥 Installing/updating requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.template .env
    echo ⚠️  Please edit .env file and add your Gemini API key!
    echo Get your API key from: https://makersuite.google.com/app/apikey
    echo.
    set /p response="Do you want to open .env file now? (y/n): "
    if /i "%response%"=="y" notepad .env
)

REM Start the application
echo 🖥️ Starting GIS Copilot Desktop...
python main.py
