# GIS Copilot Desktop

A desktop GIS application with AI-powered spatial analysis capabilities. This is a Qt-based desktop version that reads spatial files directly without requiring PostgreSQL or GeoServer.

## Features

- **🖥️ Desktop Application**: Native Qt5 interface, no web browser required
- **📁 Direct File Reading**: Load shapefiles, GeoJSON, CSV, and other formats directly
- **🤖 AI-Powered Analysis**: Ask spatial questions in natural language
- **🗺️ Interactive Maps**: Built-in map viewer using Folium
- **📊 Layer Management**: Add, remove, and style map layers
- **💾 Data Export**: Export analysis results to various formats
- **🎨 Modern UI**: Dark theme with intuitive interface

## Requirements

- Python 3.8+
- PyQt5
- GeoPandas
- Folium
- Gemini API key

## Quick Start

### 🚀 For New Users

1. **Download the project** (clone or download ZIP)
2. **Run the setup wizard**: Double-click `SETUP.bat` (Windows) or follow [INSTALLATION.md](INSTALLATION.md)
3. **Configure your API key**: Edit `.env` file with your [Gemini API key](https://aistudio.google.com/app/apikey)
4. **Start the application**: Double-click `start.bat` or run `python main.py`

> **Having installation issues?** Check our comprehensive [Installation Guide](INSTALLATION.md) which handles common SSL errors and dependency issues.

## Installation

### Automated Setup (Recommended)

**Windows Users:**
```cmd
SETUP.bat
```

**All Platforms:**
See our detailed [Installation Guide](INSTALLATION.md) for step-by-step instructions and troubleshooting.

### Manual Installation

1. **Clone or extract the project**
   ```bash
   cd gis_copilot_desktop
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux  
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   
   # If you get SSL errors, use:
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy the template and edit with your API key
   copy .env.template .env    # Windows
   cp .env.template .env      # macOS/Linux
   ```

5. **Test installation**
   ```bash
   python test_system.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

## Usage

### Loading Data
1. Use the **File Browser** panel to navigate your computer
2. Click on spatial files (highlighted in green) to load them
3. Supported formats: `.shp`, `.geojson`, `.json`, `.csv`, `.kml`, `.gpx`, `.gdb`

### AI Analysis
Ask spatial questions in the chat panel:

**Examples:**
- "Create a 500 meter buffer around the roads layer"
- "Select all buildings with type = 'residential'"
- "Find the intersection between parcels and flood zones"
- "Buffer hospitals by 1km and find overlapping areas"

### Layer Management
- Toggle layer visibility with checkboxes
- Right-click layers for context menu (export, properties, remove)
- Export layers to GeoJSON, Shapefile, or CSV

### Map Interaction
- Pan and zoom the map
- Click features to see attributes
- Layers are automatically styled based on geometry type

## Supported Spatial Operations

The AI can perform these operations:
- **Buffer**: Create buffers around features
- **Select**: Filter features by attributes
- **Intersect**: Find spatial intersections
- **Union**: Combine layer geometries
- **Dissolve**: Merge features by attribute
- **Clip**: Cut layers by boundaries

## File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Shapefile | `.shp` | Complete with .shx, .dbf files |
| GeoJSON | `.geojson`, `.json` | Web-friendly format |
| CSV | `.csv` | Must have lat/lon columns |
| KML | `.kml` | Google Earth format |
| GPX | `.gpx` | GPS track format |
| File Geodatabase | `.gdb` | ESRI format (folder) |

## Configuration

### Environment Variables (.env)
```bash
GEMINI_API_KEY=your_api_key_here
THEME=dark
```

### Config File (config/config.yaml)
```yaml
ai:
  model: "gemini-pro"
  
map:
  default_center: [24.7135, 46.6753]  # Riyadh
  default_zoom: 10
  
ui:
  theme: "dark"
```

## Architecture

```
gis_copilot_desktop/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── config/
│   └── config.yaml        # Application configuration
├── core/                  # Core functionality
│   ├── data_manager.py    # Spatial data management
│   ├── ai_agent.py        # AI spatial analysis
│   └── map_manager.py     # Map generation
└── ui/                    # User interface components
    ├── file_browser.py    # File browsing widget
    ├── chat_panel.py      # AI chat interface
    └── layer_panel.py     # Layer management widget
```

## Differences from Web Version

| Feature | Web Version | Desktop Version |
|---------|-------------|-----------------|
| Database | PostgreSQL + PostGIS | In-memory GeoPandas |
| Map Server | GeoServer | Folium HTML |
| Interface | Web browser | Qt5 desktop |
| Dependencies | Many services | Self-contained |
| Installation | Complex setup | Simple pip install |
| Performance | Server-side | Direct file access |

## Troubleshooting

### Installation Issues

**SSL Certificate Errors:**
```bash
# Use trusted hosts to bypass SSL issues
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

**PyQtWebEngine Fails to Install:**
```bash
# Use our specialized installer
.\install_webengine.bat

# Or skip it (app works with limited map features)
pip install -r requirements_minimal.txt
```

**Virtual Environment Issues:**
- Ensure Python 3.8+ is installed and in PATH
- Try running as Administrator (Windows)
- Use full Python path if needed

### Application Issues

**AI Not Working**
- Check your Gemini API key in `.env`
- Ensure internet connection for AI features
- Verify API quota/limits

**File Loading Fails**
- Check file permissions and format
- Ensure all shapefile components present (.shp, .shx, .dbf)
- For CSV files, verify lat/lon column names

**Map Not Displaying**
- Check if PyQtWebEngine is installed
- Try refreshing the map view (View → Refresh Map)

**Performance Issues**
- Large datasets may be slow to load
- Consider simplifying geometries for better performance
- Close unused layers

### Getting Help

1. **Run diagnostics**: `python test_system.py`
2. **Check our [Installation Guide](INSTALLATION.md)** for detailed troubleshooting
3. **Create an issue** with your system info and error messages

## Development

To run in development mode:
```powershell
python main.py
```

To build executable:
```powershell
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## License

Open source - feel free to use and modify.

---

**Built with ❤️ for the GIS community**
