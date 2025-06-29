@echo off
setlocal enabledelayedexpansion

echo.
echo ===============================================
echo     [*] GIS Copilot Desktop Setup Wizard
echo ===============================================
echo.
echo This script will help you set up GIS Copilot Desktop
echo with automatic handling of common installation issues.
echo.

REM Check if Python is available
echo [*] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [+] Found Python %PYTHON_VERSION%

REM Check if virtual environment exists
if exist "venv" (
    echo [*] Virtual environment already exists
    set /p recreate="Do you want to recreate it? This will reinstall all packages (y/n): "
    if /i "!recreate!"=="y" (
        echo [-] Removing old virtual environment...
        rmdir /s /q venv
    )
)

if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [X] Failed to create virtual environment
        echo.
        echo This might be due to:
        echo - Insufficient permissions
        echo - Antivirus blocking the operation
        echo - Corrupted Python installation
        echo.
        pause
        exit /b 1
    )
    echo [+] Virtual environment created successfully
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [X] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip first
echo [*] Upgrading pip and essential tools...
python -m pip install --upgrade pip setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
if %errorlevel% neq 0 (
    echo [!] Warning: Failed to upgrade pip, but continuing...
)

echo.
echo [*] Installing packages with SSL error handling...
echo This may take several minutes depending on your internet connection.
echo.

REM Try installing from requirements.txt first
echo [*] Method 1: Installing from requirements.txt with trusted hosts...
pip install --timeout 300 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

if %errorlevel% equ 0 (
    echo [+] All packages installed successfully!
    goto :check_env
)

echo [!] Standard installation failed. Trying fallback methods...
echo.

REM Fallback: Install packages individually
echo [*] Method 2: Installing packages individually...

REM Core packages that rarely fail
echo Installing core packages...
set CORE_PACKAGES=pyyaml python-dotenv packaging wheel setuptools

for %%p in (%CORE_PACKAGES%) do (
    echo   [*] Installing %%p...
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org %%p
)

REM UI packages
echo Installing UI packages...
echo   [*] Installing PyQt5 (this may take a while)...
pip install --timeout 600 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org PyQt5

echo   [*] Installing QDarkStyle...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org QDarkStyle

REM AI packages
echo Installing AI packages...
echo   [*] Installing Google Generative AI...
pip install --timeout 300 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org google-generativeai

REM Visualization packages
echo Installing visualization packages...
echo   [*] Installing matplotlib...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org matplotlib

echo   [*] Installing folium...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org folium

REM GIS packages (these can be tricky)
echo Installing GIS packages...
echo   [*] Installing shapely...
pip install --timeout 300 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org shapely

echo   [*] Installing fiona (this may take a while)...
pip install --timeout 600 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org fiona

echo   [*] Installing pyproj...
pip install --timeout 300 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org pyproj

echo   [*] Installing geopandas...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org geopandas

REM PyQtWebEngine (most problematic package)
echo.
echo [*] Installing PyQtWebEngine (web engine for maps)...
echo This is often the most problematic package due to its large size.
echo.

pip install --timeout 900 --retries 3 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org PyQtWebEngine

if %errorlevel% neq 0 (
    echo.
    echo [!] PyQtWebEngine installation failed!
    echo.
    echo This package enables web-based map rendering.
    echo The application will still work, but with limited map functionality.
    echo.
    echo You can try installing it manually later using:
    echo   .\install_webengine.bat
    echo.
    set /p continue="Continue without PyQtWebEngine? (y/n): "
    if /i not "!continue!"=="y" (
        echo Installation cancelled.
        pause
        exit /b 1
    )
)

:check_env
echo.
echo [*] Setting up configuration...

REM Create .env file from template
if not exist ".env" (
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo [+] Created .env file from template
    ) else (
        echo GEMINI_API_KEY=your_api_key_here> .env
        echo DEBUG=False>> .env
        echo LOG_LEVEL=INFO>> .env
        echo [+] Created basic .env file
    )
    
    echo.
    echo [!] IMPORTANT: You need to configure your Gemini API key!
    echo.
    echo 1. Get your API key from: https://aistudio.google.com/app/apikey
    echo 2. Edit the .env file and replace "your_api_key_here" with your actual key
    echo.
    
    set /p open_env="Do you want to open the .env file now? (y/n): "
    if /i "!open_env!"=="y" (
        notepad .env
    )
) else (
    echo [+] .env file already exists
)

echo.
echo [*] Running system test to verify installation...
echo.

python test_system.py

if %errorlevel% equ 0 (
    echo.
    echo ===============================================
    echo [+] SUCCESS! GIS Copilot Desktop is ready to use!
    echo ===============================================
    echo.
    echo To start the application, run:
    echo   start.bat
    echo.
    echo Or directly:
    echo   python main.py
    echo.
) else (
    echo.
    echo ===============================================
    echo [!] Setup completed with some issues
    echo ===============================================
    echo.
    echo Some components may not work correctly.
    echo Check the test output above for details.
    echo.
    echo You can still try running the application:
    echo   python main.py
    echo.
)

set /p run_now="Do you want to start the application now? (y/n): "
if /i "!run_now!"=="y" (
    echo.
    echo [*] Starting GIS Copilot Desktop...
    python main.py
)

echo.
echo Setup complete! Thank you for using GIS Copilot Desktop.
pause
