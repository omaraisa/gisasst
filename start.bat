@echo off
setlocal enabledelayedexpansion
echo 🚀 Starting GIS Copilot Desktop...

REM Check if this is the first run and suggest SETUP.bat
if not exist "venv" (
    echo.
    echo ⚠️  It looks like this is your first time running GIS Copilot Desktop!
    echo.
    echo For the best experience, we recommend using our automated setup:
    echo   SETUP.bat
    echo.
    echo This will handle virtual environment creation, package installation,
    echo and common issues like SSL errors automatically.
    echo.
    set /p usesetup="Do you want to run the automated setup now? (y/n): "
    if /i "!usesetup!"=="y" (
        echo.
        echo 📋 Running automated setup...
        call SETUP.bat
        exit /b 0
    ) else (
        echo.
        echo ❌ Cannot start without setup. Please run SETUP.bat first.
        pause
        exit /b 1
    )
)

REM Check if Python is available
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Python not found! Please install Python 3.8 or higher.
    echo.
    echo Download Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo � Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo ❌ Failed to activate virtual environment.
    echo.
    echo Please run SETUP.bat to create the virtual environment.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo 📝 Creating .env file from template...
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo ✅ .env file created successfully!
    ) else (
        echo GEMINI_API_KEY=your_api_key_here> .env
        echo DEBUG=False>> .env
        echo LOG_LEVEL=INFO>> .env
        echo ✅ Created basic .env file
    )
    echo.
    echo ⚠️  Important: Please edit .env file and add your Gemini API key!
    echo Get your API key from: https://aistudio.google.com/app/apikey
    echo.
    set /p response="Do you want to open .env file now? (y/n): "
    if /i "!response!"=="y" notepad .env
)

REM Start the application
echo 🖥️ Starting GIS Copilot Desktop...
start python main.py

echo.
echo ✅ Application is starting...
echo.
echo If the application window doesn't appear, check for error messages above.
echo The application runs in a separate window, so you can close this console.
echo.
pause
