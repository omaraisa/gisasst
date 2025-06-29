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
from core.logger import setup_logging, get_logger, log_system_info, cleanup_old_logs
from ui.file_browser import FileBrowser
from ui.chat_panel import ChatPanel
from ui.layer_panel import LayerPanel

class GISCopilotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize logging first
        self.setup_logging()
        self.logger = get_logger(__name__)
        
        self.logger.info("Starting GIS Copilot Desktop application")
        log_system_info(self.logger)
        
        self.setWindowTitle("GIS Copilot Desktop")
        self.setGeometry(100, 100, 1400, 900)
        
        try:
            # Load configuration
            load_dotenv()
            self.config = self.load_config()
            
            # Initialize core components
            self.data_manager = DataManager()
            self.ai_agent = AIAgent(self.config)
            self.map_manager = MapManager()
            
            self.init_ui()
            self.setup_connections()
            
            self.logger.info("Application initialization completed successfully")
            
        except Exception as e:
            self.logger.exception("Failed to initialize application")
            QMessageBox.critical(None, "Initialization Error", 
                               f"Failed to initialize application: {str(e)}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Get log level from environment or default to INFO
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Setup logging
        self.main_logger, self.log_file = setup_logging(
            log_level=log_level,
            log_to_file=True,
            log_to_console=True
        )
        
        # Clean up old logs
        cleanup_old_logs(max_age_days=30)
        
    def load_config(self):
        """Load configuration from YAML file"""
        self.logger.info("Loading configuration...")
        config_path = Path(__file__).parent / "config" / "config.yaml"
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}")
                config = self._get_default_config()
        else:
            self.logger.info("Config file not found, using default configuration")
            config = self._get_default_config()
            
        return config
    
    def _get_default_config(self):
        """Get default configuration"""
        return {
            "ai": {
                "model": "gemini-1.5-flash-latest",
                "api_key": os.getenv("GEMINI_API_KEY", "")
            },
            "map": {
                "default_center": [24.7135, 46.6753],  # Riyadh
                "default_zoom": 10
            }
        }
        
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(main_splitter)
        
        # Left panel - File browser and layer controls
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        # File browser
        self.file_browser = FileBrowser(self.data_manager)
        left_layout.addWidget(self.file_browser)
        
        # Layer panel
        self.layer_panel = LayerPanel(self.data_manager, self.map_manager)
        left_layout.addWidget(self.layer_panel)
        
        main_splitter.addWidget(left_panel)
        
        # Center panel - Map view
        self.map_view = QWebEngineView()
        main_splitter.addWidget(self.map_view)
        
        # Right panel - AI Chat
        right_panel = QWidget()
        right_panel.setMaximumWidth(400)
        right_panel.setMinimumWidth(350)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Chat panel takes full height
        self.chat_panel = ChatPanel(self.ai_agent, self.data_manager, self.map_manager)
        right_layout.addWidget(self.chat_panel)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions: left(350) + center(expand) + right(400)
        main_splitter.setSizes([350, 650, 400])
        
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
        self.layer_panel.zoom_to_layer_requested.connect(self.zoom_to_layer)
        
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
        self.logger.info(f"Loading spatial file: {file_path}")
        try:
            self.statusBar().showMessage(f"Loading {file_path}...")
            success = self.data_manager.load_file(file_path)
            if success:
                self.statusBar().showMessage(f"Successfully loaded {os.path.basename(file_path)}", 3000)
                self.logger.info(f"Successfully loaded spatial file: {os.path.basename(file_path)}")
            else:
                self.statusBar().showMessage("Failed to load file", 3000)
                self.logger.error(f"Failed to load spatial file: {os.path.basename(file_path)}")
                QMessageBox.warning(self, "Error", f"Failed to load {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.exception(f"Error loading spatial file {file_path}")
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
        
    def zoom_to_layer(self, layer_name):
        """Zoom map to specific layer"""
        self.logger.info(f"Zooming to layer: {layer_name}")
        try:
            # Generate map HTML zoomed to the specific layer
            html_content = self.map_manager.generate_map_html_zoomed_to_layer(
                self.data_manager.get_layers(),
                layer_name,
                self.config["map"]["default_center"],
                self.config["map"]["default_zoom"]
            )
            self.map_view.setHtml(html_content)
            self.statusBar().showMessage(f"Zoomed to layer '{layer_name}'", 3000)
            self.logger.info(f"Successfully zoomed to layer: {layer_name}")
        except Exception as e:
            self.logger.exception(f"Failed to zoom to layer '{layer_name}'")
            QMessageBox.warning(self, "Zoom Error", f"Failed to zoom to layer '{layer_name}': {str(e)}")
            self.statusBar().showMessage("Zoom failed", 3000)
        
def main():
    app = QApplication(sys.argv)
    
    # Apply dark theme
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    except ImportError:
        pass  # Use default theme if qdarkstyle not available
    
    try:
        window = GISCopilotApp()
        window.show()
        
        # Log application start
        logger = get_logger('main')
        logger.info("GIS Copilot Desktop application started successfully")
        
        result = app.exec_()
        
        logger.info("GIS Copilot Desktop application closed")
        return result
        
    except Exception as e:
        # If we don't have a logger yet, print to console
        try:
            logger = get_logger('main')
            logger.exception("Fatal error starting application")
        except:
            print(f"Fatal error starting application: {e}")
        
        QMessageBox.critical(None, "Fatal Error", f"Failed to start application: {str(e)}")
        return 1

if __name__ == "__main__":
    main()
