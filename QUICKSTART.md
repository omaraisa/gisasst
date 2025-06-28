# 🚀 Quick Start Guide

Welcome to GIS Copilot Desktop! This guide will get you up and running in 5 minutes.

## 🎯 What You'll Need

- Python 3.8 or higher ([Download here](https://www.python.org/downloads/))
- A Gemini API key ([Get one free here](https://makersuite.google.com/app/apikey))

## ⚡ Super Quick Setup

### Windows Users (Easy Way)
1. **Double-click `SETUP.bat`** - This handles everything automatically!
2. **Edit `.env` file** - Add your Gemini API key
3. **Double-click `start.bat`** - Launch the application!

### All Platforms (Manual Way)
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate     # Windows
source venv/bin/activate  # macOS/Linux

# 3. Install packages (with SSL error handling)
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# 4. Set up config
copy .env.template .env   # Windows
cp .env.template .env     # macOS/Linux

# 5. Run the app
python main.py
```

## 🔑 Configure Your API Key

1. Get your **free** Gemini API key: https://makersuite.google.com/app/apikey
2. Open the `.env` file in any text editor
3. Replace `your_api_key_here` with your actual API key:
   ```
   GEMINI_API_KEY=AIzaSyAb...your-actual-key-here
   ```
4. Save the file

## 🎉 First Steps

1. **Load some data**: Use the file browser to open shapefiles, GeoJSON, or CSV files
2. **Ask questions**: Try "Create a 500m buffer around the roads"
3. **Explore the map**: Click and zoom around your data
4. **Export results**: Right-click layers to export your analysis

## 📁 Test Data

Don't have GIS data? Try these free sources:
- **Natural Earth**: https://www.naturalearthdata.com/
- **OpenStreetMap**: https://download.geofabrik.de/
- **Government Data**: Many countries provide free GIS data

## ❓ Having Issues?

### Common Problems & Solutions

**"Python not found"**
- Install Python from python.org
- Make sure to check "Add Python to PATH"

**SSL/Certificate errors**
- Run `SETUP.bat` which handles this automatically
- Or see our [Installation Guide](INSTALLATION.md)

**PyQtWebEngine won't install**
- Run `install_webengine.bat`
- Or continue without it (maps will be limited)

**API not working**
- Check your API key in `.env`
- Make sure you have internet connection

### Need More Help?

- 📖 **Detailed guide**: [INSTALLATION.md](INSTALLATION.md)
- 🧪 **Test your setup**: Run `python test_system.py`
- 📋 **Full documentation**: [README.md](README.md)

## 🎮 Try These Examples

Once running, ask the AI assistant:

```
"Load the cities dataset and show me all cities with population > 100000"

"Create a 1km buffer around hospitals and find intersections with schools"

"Calculate the area of each park and export to CSV"

"Show me a heatmap of crime incidents by neighborhood"
```

---

**Ready to explore? Let's go! 🗺️✨**

> **Pro tip**: Start with the automated `SETUP.bat` - it handles 99% of installation issues automatically!
