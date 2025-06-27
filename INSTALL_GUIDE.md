# 🚀 GIS Copilot Desktop - Quick Installation Guide

## Prerequisites
- **Python 3.8 or higher** ([Download here](https://www.python.org/downloads/))
- **Windows 10/11** (tested platform)
- **Google Gemini API Key** ([Get free key](https://makersuite.google.com/app/apikey))

## ⚡ Quick Install (Recommended)

### 1. Run the Automated Setup
```powershell
# Navigate to the project folder
cd gis_copilot_desktop

# Run the setup script (this handles everything)
.\start.ps1
```

The setup script will:
- ✅ Create Python virtual environment
- ✅ Install all required packages
- ✅ Set up configuration files
- ✅ Prompt for API key setup
- ✅ Launch the application

### 2. Configure Your API Key
When prompted, or manually edit `.env`:
```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Done! 🎉
The application should launch automatically.

## 🛠️ Manual Installation

If the automated setup doesn't work, follow these steps:

### Step 1: Create Virtual Environment
```bash
python -m venv venv
```

### Step 2: Activate Virtual Environment
```bash
# Windows Command Prompt
venv\Scripts\activate

# Windows PowerShell  
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
copy .env.template .env
# Edit .env file and add your Gemini API key
```

### Step 5: Run Application
```bash
python main.py
```

## 📦 Required Packages

The application will install these packages automatically:

### Core Framework
- **PyQt5** - Desktop GUI framework
- **PyQtWebEngine** - Web content integration

### Spatial Processing
- **geopandas** - Spatial data manipulation
- **shapely** - Geometric operations
- **fiona** - Spatial file I/O
- **pyproj** - Coordinate system transformations

### AI & Visualization
- **google-generativeai** - AI analysis capabilities
- **folium** - Interactive map generation
- **matplotlib** - Data visualization

### Utilities
- **pyyaml** - Configuration file handling
- **python-dotenv** - Environment variable management

## 🧪 Test Your Installation

### Run System Test
```bash
python test_system.py
```

This will check:
- ✅ Python version compatibility
- ✅ All required packages installed
- ✅ Qt display capability
- ✅ Configuration files present
- ✅ Spatial data processing
- ✅ AI connection (if API key configured)

### Run Interactive Demo
```bash
python interactive_demo.py
```

Shows application features and structure without requiring full installation.

## 🆘 Common Installation Issues

### Issue: "Python not found"
**Solution:**
1. Install Python from [python.org](https://python.org)
2. During installation, check "Add Python to PATH"
3. Restart command prompt/PowerShell

### Issue: "PyQt5 installation fails"
**Solution:**
```bash
# Try installing with different options
pip install --user PyQt5
# Or use conda
conda install pyqt
```

### Issue: "SSL certificate errors"
**Solution:**
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Issue: "Virtual environment activation fails"
**Solution:**
```bash
# Enable script execution in PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "Spatial libraries fail to install"
**Solutions:**
1. **Use conda instead of pip:**
   ```bash
   conda install geopandas
   ```

2. **Install pre-compiled wheels:**
   ```bash
   pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/ geopandas
   ```

3. **Use minimal installation:**
   ```bash
   pip install pandas shapely fiona pyproj
   pip install geopandas --no-deps
   ```

## 🔧 Alternative Installation Methods

### Option 1: Using Conda
```bash
# Create conda environment
conda create -n gis_copilot python=3.9
conda activate gis_copilot

# Install spatial packages
conda install -c conda-forge geopandas
conda install -c conda-forge folium

# Install remaining packages with pip
pip install PyQt5 google-generativeai python-dotenv pyyaml
```

### Option 2: Docker (Advanced)
```dockerfile
# Future enhancement - containerized version
FROM python:3.9-slim
# ... (Docker setup for desktop apps requires X11 forwarding)
```

## 📋 Verification Checklist

After installation, verify these work:

- [ ] **Python version**: `python --version` shows 3.8+
- [ ] **Virtual environment**: Activated successfully
- [ ] **Dependencies**: All packages installed without errors
- [ ] **Configuration**: `.env` file exists with API key
- [ ] **Application launch**: `python main.py` starts GUI
- [ ] **File loading**: Can browse and load spatial files
- [ ] **AI features**: Chat panel responds to questions
- [ ] **Map display**: Interactive map shows in right panel

## 🎯 Next Steps

After successful installation:

1. **Load Sample Data**: Use File Browser to load a shapefile or GeoJSON
2. **Try AI Analysis**: Ask "Create a buffer around the loaded features"
3. **Explore Features**: Test layer management and export capabilities
4. **Read Documentation**: Check README.md for detailed usage guide

## 🆔 Getting Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key
5. Add to `.env` file: `GEMINI_API_KEY=your_key_here`

**Note:** The API key is free for reasonable usage limits.

## 📞 Support

If you encounter issues:

1. **Run system test**: `python test_system.py`
2. **Check error messages** in terminal output
3. **Verify Python version** compatibility
4. **Check internet connection** for package downloads
5. **Review installation logs** for specific error details

---

**🎉 Once installed, you'll have a powerful desktop GIS application with AI-powered spatial analysis capabilities!**
