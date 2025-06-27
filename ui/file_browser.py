from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QLabel, 
                             QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import os
from pathlib import Path

class FileBrowser(QWidget):
    """File browser widget for navigating and loading spatial files"""
    
    file_selected = pyqtSignal(str)  # file_path
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.current_path = Path.home()
        
        self.init_ui()
        self.refresh_files()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("📁 File Browser")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self.path_edit = QLineEdit(str(self.current_path))
        self.path_edit.returnPressed.connect(self.navigate_to_path)
        nav_layout.addWidget(self.path_edit)
        
        up_btn = QPushButton("↑")
        up_btn.setMaximumWidth(30)
        up_btn.setToolTip("Go up one directory")
        up_btn.clicked.connect(self.go_up)
        nav_layout.addWidget(up_btn)
        
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(30)
        browse_btn.setToolTip("Browse for folder")
        browse_btn.clicked.connect(self.browse_folder)
        nav_layout.addWidget(browse_btn)
        
        layout.addLayout(nav_layout)
        
        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Type"])
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.file_tree.setAlternatingRowColors(True)
        layout.addWidget(self.file_tree)
        
        # Load button
        load_btn = QPushButton("Load Selected File")
        load_btn.clicked.connect(self.load_selected_file)
        layout.addWidget(load_btn)
        
        # Supported formats info
        info_label = QLabel("Supported: .shp, .geojson, .json, .csv, .kml, .gpx, .gdb")
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
    def refresh_files(self):
        """Refresh the file tree"""
        self.file_tree.clear()
        self.path_edit.setText(str(self.current_path))
        
        try:
            if not self.current_path.exists():
                self.current_path = Path.home()
                self.path_edit.setText(str(self.current_path))
            
            # Add directories first
            for item in sorted(self.current_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    tree_item = QTreeWidgetItem([item.name, "Folder"])
                    tree_item.setData(0, Qt.UserRole, str(item))
                    tree_item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                    self.file_tree.addTopLevelItem(tree_item)
            
            # Add files
            spatial_extensions = {'.shp', '.geojson', '.json', '.csv', '.kml', '.gpx', '.gdb'}
            
            for item in sorted(self.current_path.iterdir()):
                if item.is_file():
                    is_spatial = item.suffix.lower() in spatial_extensions
                    
                    tree_item = QTreeWidgetItem([item.name, "Spatial File" if is_spatial else "File"])
                    tree_item.setData(0, Qt.UserRole, str(item))
                    
                    if is_spatial:
                        tree_item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                        # Highlight spatial files
                        tree_item.setBackground(0, tree_item.background(0).color().lighter(120))
                    else:
                        tree_item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                        # Dim non-spatial files
                        tree_item.setDisabled(True)
                    
                    self.file_tree.addTopLevelItem(tree_item)
                    
        except PermissionError:
            QMessageBox.warning(self, "Permission Error", "Cannot access this directory.")
            self.current_path = Path.home()
            self.refresh_files()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reading directory: {str(e)}")
    
    def on_item_double_clicked(self, item, column):
        """Handle double-click on tree item"""
        file_path = Path(item.data(0, Qt.UserRole))
        
        if file_path.is_dir():
            self.current_path = file_path
            self.refresh_files()
        elif file_path.is_file():
            self.load_file(str(file_path))
    
    def load_selected_file(self):
        """Load the currently selected file"""
        current_item = self.file_tree.currentItem()
        if current_item:
            file_path = Path(current_item.data(0, Qt.UserRole))
            if file_path.is_file():
                self.load_file(str(file_path))
            else:
                QMessageBox.information(self, "Info", "Please select a file to load.")
        else:
            QMessageBox.information(self, "Info", "Please select a file to load.")
    
    def load_file(self, file_path):
        """Load a spatial file"""
        try:
            success = self.data_manager.load_file(file_path)
            if success:
                self.file_selected.emit(file_path)
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Successfully loaded {os.path.basename(file_path)}"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Failed to load {os.path.basename(file_path)}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def go_up(self):
        """Go up one directory level"""
        parent = self.current_path.parent
        if parent != self.current_path:  # Prevent going above root
            self.current_path = parent
            self.refresh_files()
    
    def navigate_to_path(self):
        """Navigate to the path in the text field"""
        try:
            new_path = Path(self.path_edit.text())
            if new_path.exists() and new_path.is_dir():
                self.current_path = new_path
                self.refresh_files()
            else:
                QMessageBox.warning(self, "Invalid Path", "The specified path does not exist or is not a directory.")
                self.path_edit.setText(str(self.current_path))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error navigating to path: {str(e)}")
            self.path_edit.setText(str(self.current_path))
    
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder",
            str(self.current_path)
        )
        
        if folder:
            self.current_path = Path(folder)
            self.refresh_files()
    
    def set_root_path(self, path):
        """Set the root path for browsing"""
        try:
            self.current_path = Path(path)
            self.refresh_files()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting path: {str(e)}")
