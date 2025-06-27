import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QSplitter, QTreeWidget, QTreeWidgetItem, 
                             QTextEdit, QLineEdit, QPushButton, QTabWidget, 
                             QListWidget, QFileDialog, QMessageBox, QLabel,
                             QProgressBar, QToolBar, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
import geopandas as gpd
import folium
import tempfile
import json
from pathlib import Path
import yaml
from dotenv import load_dotenv

from core.data_manager import DataManager
from core.ai_agent import AIAgent
from core.map_manager import MapManager
from ui.file_browser import FileBrowser
from ui.chat_panel import ChatPanel
from ui.layer_panel import LayerPanel

class GISCopilotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIS Copilot Desktop")
        self.setGeometry(100, 100, 1400, 900)
        
        # Load configuration
        load_dotenv()
        self.config = self.load_config()
        
        # Initialize core components
        self.data_manager = DataManager()
        self.ai_agent = AIAgent(self.config)
        self.map_manager = MapManager()
        
        self.init_ui()
        self.setup_connections()
        
    def load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = {
                "ai": {
                    "model": "gemini-pro",
                    "api_key": os.getenv("GEMINI_API_KEY", "")
                },
                "map": {
                    "default_center": [24.7135, 46.6753],  # Riyadh
                    "default_zoom": 10
                }
            }
        return config
        
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(main_splitter)
        
        # Left panel - File browser and controls
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        # File browser
        self.file_browser = FileBrowser(self.data_manager)
        left_layout.addWidget(self.file_browser)
        
        # Layer panel
        self.layer_panel = LayerPanel(self.data_manager, self.map_manager)
        left_layout.addWidget(self.layer_panel)
        
        # Chat panel
        self.chat_panel = ChatPanel(self.ai_agent, self.data_manager, self.map_manager)
        left_layout.addWidget(self.chat_panel)
        
        main_splitter.addWidget(left_panel)
        
        # Right panel - Map view
        self.map_view = QWebEngineView()
        main_splitter.addWidget(self.map_view)
        
        # Set splitter proportions
        main_splitter.setSizes([350, 1050])
        
        # Initialize map
        self.init_map()
        
        # Setup menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open File', self)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction('Open Folder', self)
        open_folder_action.triggered.connect(self.open_folder_dialog)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        refresh_action = QAction('Refresh Map', self)
        refresh_action.triggered.connect(self.refresh_map)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def init_map(self):
        """Initialize the map view"""
        self.update_map()
        
    def update_map(self):
        """Update the map with current layers"""
        html_content = self.map_manager.generate_map_html(
            self.data_manager.get_layers(),
            self.config["map"]["default_center"],
            self.config["map"]["default_zoom"]
        )
        self.map_view.setHtml(html_content)
        
    def refresh_map(self):
        """Refresh the map view"""
        self.update_map()
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Connect data manager signals
        self.data_manager.layer_added.connect(self.on_layer_added)
        self.data_manager.layer_removed.connect(self.on_layer_removed)
        
        # Connect chat panel signals
        self.chat_panel.map_update_requested.connect(self.update_map)
        
        # Connect layer panel signals
        self.layer_panel.layer_visibility_changed.connect(self.update_map)
        
    def on_layer_added(self, layer_name):
        """Handle layer added event"""
        self.layer_panel.refresh_layers()
        self.update_map()
        self.statusBar().showMessage(f"Layer '{layer_name}' added successfully", 3000)
        
    def on_layer_removed(self, layer_name):
        """Handle layer removed event"""
        self.layer_panel.refresh_layers()
        self.update_map()
        self.statusBar().showMessage(f"Layer '{layer_name}' removed", 3000)
        
    def open_file_dialog(self):
        """Open file dialog for spatial files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Spatial File",
            "",
            "Spatial Files (*.shp *.geojson *.json *.csv *.kml *.gpx);;All Files (*)"
        )
        
        if file_path:
            self.load_spatial_file(file_path)
            
    def open_folder_dialog(self):
        """Open folder dialog"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.file_browser.set_root_path(folder_path)
            
    def load_spatial_file(self, file_path):
        """Load a spatial file"""
        try:
            self.statusBar().showMessage(f"Loading {file_path}...")
            success = self.data_manager.load_file(file_path)
            if success:
                self.statusBar().showMessage(f"Successfully loaded {os.path.basename(file_path)}", 3000)
            else:
                self.statusBar().showMessage("Failed to load file", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            self.statusBar().showMessage("Error loading file", 3000)
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About GIS Copilot Desktop",
            "GIS Copilot Desktop v1.0\n\n"
            "A desktop GIS application with AI-powered spatial analysis.\n"
            "Built with PyQt5 and powered by Gemini AI."
        )
        
def main():
    app = QApplication(sys.argv)
    
    # Apply dark theme
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    except ImportError:
        pass  # Use default theme if qdarkstyle not available
    
    window = GISCopilotApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
