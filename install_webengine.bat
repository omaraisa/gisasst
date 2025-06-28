@echo off
echo 🌐 PyQtWebEngine Installation Helper
echo.
echo This script provides alternative methods to install PyQtWebEngine
echo which often fails due to SSL/network issues.
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 📚 Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo Method 1: Installing with trusted hosts and extended timeout...
pip install --timeout 600 --retries 5 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org PyQtWebEngine

if %errorlevel% neq 0 (
    echo.
    echo Method 2: Installing with no cache and force reinstall...
    pip install --no-cache-dir --force-reinstall --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org PyQtWebEngine
    
    if %errorlevel% neq 0 (
        echo.
        echo Method 3: Installing from wheel file...
        echo Downloading wheel file manually...
        
        REM Try to download the wheel directly
        python -c "
import requests
import platform
import sys

# Determine the correct wheel for Windows
if platform.machine().endswith('64'):
    arch = 'win_amd64'
else:
    arch = 'win32'

python_version = f'{sys.version_info.major}{sys.version_info.minor}'
url = f'https://files.pythonhosted.org/packages/cp{python_version}/PyQtWebEngine_Qt5-5.15.2-cp{python_version}-cp{python_version}-{arch}.whl'

print(f'Attempting to download: {url}')
try:
    response = requests.get(url, timeout=300)
    if response.status_code == 200:
        with open('PyQtWebEngine.whl', 'wb') as f:
            f.write(response.content)
        print('Download successful!')
    else:
        print(f'Download failed with status: {response.status_code}')
except Exception as e:
    print(f'Download error: {e}')
"
        
        if exist "PyQtWebEngine.whl" (
            echo Installing from local wheel file...
            pip install PyQtWebEngine.whl
            del PyQtWebEngine.whl
        ) else (
            echo.
            echo ❌ All automatic methods failed.
            echo.
            echo 💡 Manual alternatives:
            echo 1. Try again later when network conditions are better
            echo 2. Use conda instead: conda install pyqtwebengine
            echo 3. Download wheel manually from https://pypi.org/project/PyQtWebEngine/#files
            echo 4. The application can run without PyQtWebEngine (web features will be limited)
            echo.
        )
    )
)

if %errorlevel% equ 0 (
    echo ✅ PyQtWebEngine installed successfully!
) else (
    echo ⚠️  PyQtWebEngine installation incomplete
)

echo.
pause
