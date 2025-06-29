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
        up_btn.setMaximumWidth(40)
        up_btn.setMaximumHeight(32)
        up_btn.setStyleSheet("QPushButton { padding: 8px; font-size: 12px; }")
        up_btn.setToolTip("Go up one directory")
        up_btn.clicked.connect(self.go_up)
        nav_layout.addWidget(up_btn)
        
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(40)
        browse_btn.setMaximumHeight(32)
        browse_btn.setStyleSheet("QPushButton { padding: 8px; font-size: 12px; }")
        browse_btn.setToolTip("Browse for folder")
        browse_btn.clicked.connect(self.browse_folder)
        nav_layout.addWidget(browse_btn)
        
        layout.addLayout(nav_layout)
        
        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Type"])
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.file_tree.setAlternatingRowColors(True)
        # Enable multiple selection
        self.file_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        layout.addWidget(self.file_tree)
        
        # Load button
        load_btn = QPushButton("Load Selected File(s)")
        load_btn.setStyleSheet("QPushButton { padding: 8px 16px; font-size: 12px; }")
        load_btn.clicked.connect(self.load_selected_files)
        layout.addWidget(load_btn)
        
        # Supported formats info
        info_label = QLabel("Supported: .shp, .geojson, .json, .csv, .kml, .gpx, .gdb (geodatabase)")
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
            shapefile_companion_extensions = {'.dbf', '.shx', '.prj', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', '.aih', '.ixs', '.mxs', '.atx', '.cpg', '.qix'}
            
            for item in sorted(self.current_path.iterdir()):
                if item.is_file():
                    # Skip shapefile companion files
                    if item.suffix.lower() in shapefile_companion_extensions:
                        continue
                        
                    is_spatial = item.suffix.lower() in spatial_extensions
                    
                    # For .gdb folders, show them as files
                    if item.suffix.lower() == '.gdb':
                        tree_item = QTreeWidgetItem([item.name, "Geodatabase"])
                        tree_item.setData(0, Qt.UserRole, str(item))
                        tree_item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                        tree_item.setBackground(0, tree_item.background(0).color().lighter(120))
                        self.file_tree.addTopLevelItem(tree_item)
                        continue
                    
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
            
            # Check for .gdb directories and show them as spatial files
            for item in sorted(self.current_path.iterdir()):
                if item.is_dir() and item.suffix.lower() == '.gdb':
                    tree_item = QTreeWidgetItem([item.name, "Geodatabase"])
                    tree_item.setData(0, Qt.UserRole, str(item))
                    tree_item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                    # Highlight geodatabase
                    tree_item.setBackground(0, tree_item.background(0).color().lighter(120))
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
        
        if file_path.is_dir() and not file_path.suffix.lower() == '.gdb':
            self.current_path = file_path
            self.refresh_files()
        elif file_path.is_file() or file_path.suffix.lower() == '.gdb':
            self.load_file(str(file_path))
    
    def load_selected_file(self):
        """Load the currently selected file"""
        current_item = self.file_tree.currentItem()
        if current_item:
            file_path = Path(current_item.data(0, Qt.UserRole))
            if file_path.is_file() or file_path.suffix.lower() == '.gdb':
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
                # Don't show success message box - just emit signal
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
    
    def load_selected_files(self):
        """Load all currently selected files"""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Please select one or more files to load.")
            return
        
        spatial_files = []
        for item in selected_items:
            file_path = Path(item.data(0, Qt.UserRole))
            if file_path.is_file() or file_path.suffix.lower() == '.gdb':
                spatial_files.append(str(file_path))
        
        if not spatial_files:
            QMessageBox.information(self, "Info", "Please select spatial files to load.")
            return
        
        # Load each file
        loaded_count = 0
        failed_files = []
        
        for file_path in spatial_files:
            try:
                success = self.data_manager.load_file(file_path)
                if success:
                    loaded_count += 1
                    self.file_selected.emit(file_path)
                else:
                    failed_files.append(os.path.basename(file_path))
            except Exception as e:
                failed_files.append(f"{os.path.basename(file_path)} ({str(e)})")
        
        # Show summary
        if loaded_count > 0:
            if failed_files:
                QMessageBox.warning(
                    self, 
                    "Partial Success", 
                    f"Loaded {loaded_count} file(s) successfully.\n\nFailed to load:\n" + 
                    "\n".join(failed_files[:5]) + ("..." if len(failed_files) > 5 else "")
                )
            # If all successful, no popup message - just status updates
        else:
            QMessageBox.critical(
                self, 
                "Error", 
                "Failed to load any selected files:\n" + 
                "\n".join(failed_files[:5]) + ("..." if len(failed_files) > 5 else "")
            )
