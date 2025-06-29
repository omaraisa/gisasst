# 🚀 Installation Guide - GIS Copilot Desktop

This guide will help you install and set up GIS Copilot Desktop on your computer, even if you encounter common installation issues.

## 📋 Prerequisites

### Required Software
- **Python 3.8 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **Git** (optional) - For cloning the repository

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 4GB (8GB+ recommended for large datasets)
- **Disk Space**: ~2GB for installation
- **Internet Connection**: Required for initial setup and AI features

## 📥 Quick Installation (Recommended)

### Option 1: Automated Setup (Windows)

1. **Download or clone the project**
   ```bash
   git clone <repository-url>
   cd gis_copilot_desktop
   ```

2. **Run the setup wizard**
   ```cmd
   SETUP.bat
   ```
   
   The setup wizard will:
   - ✅ Check Python installation
   - ✅ Create virtual environment
   - ✅ Install all dependencies with SSL error handling
   - ✅ Handle common installation issues automatically
   - ✅ Set up configuration files
   - ✅ Run system tests

3. **Configure your API key**
   - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Edit the `.env` file and replace `your_api_key_here` with your actual key

4. **Start the application**
   ```cmd
   start.bat
   ```

### Option 2: Manual Installation

If the automated setup doesn't work for you:

1. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Upgrade pip and install dependencies**
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

3. **If you encounter SSL errors, use trusted hosts**
   ```bash
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

4. **Set up configuration**
   ```bash
   copy .env.template .env    # Windows
   cp .env.template .env      # macOS/Linux
   ```

5. **Test the installation**
   ```bash
   python test_system.py
   ```

## 🔧 Troubleshooting Common Issues

### SSL Certificate Errors

**Problem**: `SSL: CERTIFICATE_VERIFY_FAILED` or similar SSL errors during installation.

**Solutions**:

1. **Use trusted hosts** (recommended):
   ```bash
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org <package_name>
   ```

2. **Update certificates**:
   ```bash
   pip install --upgrade certifi
   ```

3. **Use our SSL-safe installation script**:
   ```cmd
   SETUP.bat  # Automatically handles SSL issues
   ```

### PyQtWebEngine Installation Fails

**Problem**: Large download size (60MB+) often causes timeouts or SSL errors.

**Solutions**:

1. **Use the specialized installer**:
   ```cmd
   install_webengine.bat
   ```

2. **Manual installation with extended timeout**:
   ```bash
   pip install --timeout 900 --retries 3 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org PyQtWebEngine
   ```

3. **Skip PyQtWebEngine** (app still works with limited map features):
   ```bash
   pip install -r requirements_minimal.txt
   ```

### Virtual Environment Issues

**Problem**: Cannot create or activate virtual environment.

**Solutions**:

1. **Check Python installation**:
   ```bash
   python --version
   # Should show Python 3.8+
   ```

2. **Use full path to Python**:
   ```bash
   C:\Users\[Username]\AppData\Local\Programs\Python\Python3x\python.exe -m venv venv
   ```

3. **Run as Administrator** (Windows) if permission issues occur.

### Import Errors

**Problem**: `ModuleNotFoundError` when running the application.

**Solutions**:

1. **Ensure virtual environment is activated**:
   ```bash
   # You should see (venv) in your command prompt
   venv\Scripts\activate  # Windows
   ```

2. **Reinstall problematic packages**:
   ```bash
   pip uninstall <package_name>
   pip install <package_name>
   ```

3. **Check Python path**:
   ```bash
   python -c "import sys; print(sys.executable)"
   # Should point to your venv folder
   ```

### API Key Issues

**Problem**: AI features not working, API errors.

**Solutions**:

1. **Verify API key format** in `.env`:
   ```bash
   GEMINI_API_KEY=AIzaSy...  # Should start with AIzaSy
   ```

2. **Check API key validity** at [Google AI Studio](https://aistudio.google.com/app/apikey)

3. **Verify internet connection** for AI features

### Large File Loading Issues

**Problem**: Application freezes when loading large spatial files.

**Solutions**:

1. **Simplify geometries** before loading
2. **Split large files** into smaller chunks
3. **Use file formats optimized for large data** (GeoParquet, FlatGeobuf)
4. **Increase system RAM** if possible

## 🧪 Verifying Your Installation

Run the system test to check if everything is working:

```bash
python test_system.py
```

Expected output:
```
🧪 GIS Copilot Desktop System Test
========================================
📦 Testing Python packages...
✅ All required packages installed
🔧 Testing core modules...
✅ Core modules import successfully
📁 Testing configuration files...
✅ Configuration files OK
🗺️ Testing spatial data handling...
✅ Spatial data handling OK
🖥️ Testing Qt display...
✅ Qt display capabilities OK
🤖 Testing Gemini API...
✅ Gemini API connection successful
========================================
🎯 Test Results: 6/6 passed
✅ All systems ready!
```

## 🚀 Starting the Application

### Windows
```cmd
start.bat
```

### Cross-platform
```bash
python main.py
```

## 🔄 Updating the Application

When new versions are available:

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Update dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Run system test**:
   ```bash
   python test_system.py
   ```

## 📞 Getting Help

If you're still having issues:

1. **Check the logs** in the application console
2. **Run diagnostics**:
   ```bash
   python test_system.py --verbose
   ```
3. **Create an issue** on the project repository with:
   - Your operating system
   - Python version (`python --version`)
   - Error messages
   - Output from `python test_system.py`

## 📁 Project Structure

After successful installation, your directory should look like:

```
gis_copilot_desktop/
├── 📁 venv/                    # Virtual environment (created)
├── 📄 .env                     # Your configuration (created)
├── 📄 main.py                  # Main application
├── 📄 requirements.txt         # Package dependencies
├── 📄 SETUP.bat               # Setup wizard
├── 📄 start.bat               # Quick start script
├── 📁 config/                 # Configuration files
├── 📁 core/                   # Core functionality
└── 📁 ui/                     # User interface
```

## 🎯 Next Steps

Once installation is complete:

1. **🔑 Configure your Gemini API key** in `.env`
2. **📁 Prepare some spatial data** to test with
3. **🚀 Start the application** with `start.bat`
4. **📖 Read the README.md** for usage instructions

---

**Happy mapping! 🗺️✨**
