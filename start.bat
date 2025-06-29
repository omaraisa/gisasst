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
        if !errorlevel! equ 0 (
            echo.
            echo ✅ Setup completed successfully! Starting application...
            echo.
        ) else (
            echo.
            echo ❌ Setup failed. Please check the error messages above.
            pause
            exit /b 1
        )
    ) else (
        echo.
        echo Continuing with manual setup...
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

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo ❌ Failed to create virtual environment
        echo.
        echo 💡 Possible solutions:
        echo    1. Make sure Python is properly installed
        echo    2. Run as Administrator if needed
        echo    3. Check if antivirus is blocking the operation
        echo.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 📚 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements with SSL error handling
echo 📥 Installing/updating requirements...

REM First try with trusted hosts (bypass SSL issues)
echo 🔒 Attempting installation with trusted hosts...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

if !errorlevel! neq 0 (
    echo ⚠️  First attempt failed, trying with timeout and retry...
    
    REM Try with increased timeout and retries
    pip install --timeout 300 --retries 5 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
    
    if !errorlevel! neq 0 (
        echo ⚠️  Standard installation failed, trying individual packages...
        
        REM Install packages one by one to identify problematic ones
        echo 📦 Installing PyQt5...
        pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org PyQt5
        
        echo 📦 Installing geopandas...
        pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org geopandas
        
        echo 📦 Installing other packages...
        pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org shapely fiona pyproj google-generativeai pyyaml python-dotenv matplotlib folium QDarkStyle
        
        echo ⚠️  Attempting PyQtWebEngine installation (this may take a while)...
        pip install --timeout 600 --retries 3 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org PyQtWebEngine
          if !errorlevel! neq 0 (
            echo ❌ PyQtWebEngine installation failed. The application will still work but web features may be limited.
            echo.
            echo 💡 Common solutions:
            echo    1. Run: install_webengine.bat
            echo    2. Check INSTALLATION.md for detailed troubleshooting
            echo    3. Continue without PyQtWebEngine (app still works!)
            echo.
            set /p response="Continue without PyQtWebEngine? (y/n): "
            if /i not "!response!"=="y" (
                echo.
                echo 📖 For detailed installation help, see:
                echo    INSTALLATION.md
                echo    QUICKSTART.md  
                echo.
                pause
                exit /b 1
            )
        )
    )
)

REM Check if .env exists
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.template .env
    echo ✅ .env file created successfully!
    echo.
    echo ⚠️  Important: Please edit .env file and add your Gemini API key!
    echo Get your API key from: https://aistudio.google.com/app/apikey
    echo.
    set /p response="Do you want to open .env file now? (y/n): "
    if /i "!response!"=="y" notepad .env
)

REM Start the application
echo 🖥️ Starting GIS Copilot Desktop...
python main.py

if !errorlevel! neq 0 (
    echo.
    echo ❌ Application failed to start. Error code: !errorlevel!
    echo.
    echo 💡 Common solutions:
    echo    1. Check if all packages installed correctly
    echo    2. Verify your .env file has a valid API key  
    echo    3. Run the test script: python test_app_startup.py
    echo    4. Check INSTALLATION.md for troubleshooting
    echo.
    echo 📖 For help, see: QUICKSTART.md or INSTALLATION.md
    echo.
    pause
    exit /b !errorlevel!
)

echo.
echo ✅ Application started successfully!
echo.
echo If the application window doesn't appear, check the console for error messages.
echo To close this window, you can press any key after the application starts.
echo.
pause
