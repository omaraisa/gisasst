from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QPushButton, QLabel, QCheckBox,
                             QMenu, QAction, QMessageBox, QFileDialog,
                             QInputDialog, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
import os

class LayerPanel(QWidget):
    """Panel for managing map layers"""
    
    layer_visibility_changed = pyqtSignal()
    
    def __init__(self, data_manager, map_manager):
        super().__init__()
        self.data_manager = data_manager
        self.map_manager = map_manager
        
        self.init_ui()
        self.setup_connections()
        self.refresh_layers()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("🗺️ Layers")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layer_list.setAlternatingRowColors(True)
        layout.addWidget(self.layer_list)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_selected_layer)
        self.remove_button.setEnabled(False)
        button_layout.addWidget(self.remove_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_selected_layer)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        # Layer info
        self.info_label = QLabel("No layers loaded")
        self.info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.data_manager.layer_added.connect(self.refresh_layers)
        self.data_manager.layer_removed.connect(self.refresh_layers)
        self.data_manager.layer_updated.connect(self.refresh_layers)
        
        self.layer_list.itemChanged.connect(self.on_item_changed)
        self.layer_list.currentItemChanged.connect(self.on_selection_changed)
        
    def refresh_layers(self):
        """Refresh the layer list"""
        self.layer_list.clear()
        
        layers = self.data_manager.get_layers()
        
        if not layers:
            self.info_label.setText("No layers loaded")
            self.remove_button.setEnabled(False)
            self.export_button.setEnabled(False)
            return
            
        for layer_name, layer_data in layers.items():
            item = QListWidgetItem()
            item.setText(layer_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if layer_data.get('visible', True) else Qt.Unchecked)
            item.setData(Qt.UserRole, layer_name)
            
            # Set icon based on geometry type
            gdf = layer_data['gdf']
            if not gdf.empty:
                geom_type = gdf.geometry.geom_type.iloc[0]
                if geom_type in ['Point', 'MultiPoint']:
                    item.setText(f"📍 {layer_name}")
                elif geom_type in ['LineString', 'MultiLineString']:
                    item.setText(f"📏 {layer_name}")
                else:
                    item.setText(f"🔷 {layer_name}")
            
            self.layer_list.addItem(item)
        
        # Update info
        total_layers = len(layers)
        visible_layers = sum(1 for layer in layers.values() if layer.get('visible', True))
        self.info_label.setText(f"{total_layers} layers ({visible_layers} visible)")
        
    def on_item_changed(self, item):
        """Handle item check state change"""
        layer_name = item.data(Qt.UserRole)
        visible = item.checkState() == Qt.Checked
        
        self.data_manager.set_layer_visibility(layer_name, visible)
        self.layer_visibility_changed.emit()
        
        # Update info
        self.refresh_layers()
        
    def on_selection_changed(self, current, previous):
        """Handle selection change"""
        has_selection = current is not None
        self.remove_button.setEnabled(has_selection)
        self.export_button.setEnabled(has_selection)
        
        if current:
            layer_name = current.data(Qt.UserRole)
            layer_info = self.data_manager.get_layer_info(layer_name)
            if layer_info:
                info_text = (f"Selected: {layer_name}\n"
                           f"Type: {layer_info['geometry_type']}\n"
                           f"Features: {layer_info['feature_count']}\n"
                           f"Source: {os.path.basename(layer_info['source'])}")
                self.info_label.setText(info_text)
        else:
            layers = self.data_manager.get_layers()
            if layers:
                total_layers = len(layers)
                visible_layers = sum(1 for layer in layers.values() if layer.get('visible', True))
                self.info_label.setText(f"{total_layers} layers ({visible_layers} visible)")
            else:
                self.info_label.setText("No layers loaded")
                
    def show_context_menu(self, position):
        """Show context menu for layer operations"""
        item = self.layer_list.itemAt(position)
        if not item:
            return
            
        layer_name = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        # Zoom to layer
        zoom_action = QAction("🔍 Zoom to Layer", self)
        zoom_action.triggered.connect(lambda: self.zoom_to_layer(layer_name))
        menu.addAction(zoom_action)
        
        menu.addSeparator()
        
        # Toggle visibility
        layer_data = self.data_manager.get_layer(layer_name)
        if layer_data:
            visible = layer_data.get('visible', True)
            visibility_action = QAction(f"👁️ {'Hide' if visible else 'Show'} Layer", self)
            visibility_action.triggered.connect(lambda: self.toggle_layer_visibility(layer_name))
            menu.addAction(visibility_action)
        
        menu.addSeparator()
        
        # Properties
        properties_action = QAction("📋 Properties", self)
        properties_action.triggered.connect(lambda: self.show_layer_properties(layer_name))
        menu.addAction(properties_action)
        
        # Export
        export_action = QAction("💾 Export Layer", self)
        export_action.triggered.connect(lambda: self.export_layer(layer_name))
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # Remove
        remove_action = QAction("🗑️ Remove Layer", self)
        remove_action.triggered.connect(lambda: self.remove_layer(layer_name))
        menu.addAction(remove_action)
        
        menu.exec_(self.layer_list.mapToGlobal(position))
        
    def zoom_to_layer(self, layer_name):
        """Zoom map to layer extent"""
        # This would require communication with the map
        # For now, just show a message
        QMessageBox.information(self, "Zoom", f"Zoom to {layer_name} (feature not implemented)")
        
    def toggle_layer_visibility(self, layer_name):
        """Toggle layer visibility"""
        layer_data = self.data_manager.get_layer(layer_name)
        if layer_data:
            current_visibility = layer_data.get('visible', True)
            self.data_manager.set_layer_visibility(layer_name, not current_visibility)
            self.layer_visibility_changed.emit()
            
    def show_layer_properties(self, layer_name):
        """Show layer properties dialog"""
        layer_info = self.data_manager.get_layer_info(layer_name)
        if not layer_info:
            return
            
        properties = [
            f"Name: {layer_info['name']}",
            f"Geometry Type: {layer_info['geometry_type']}",
            f"Feature Count: {layer_info['feature_count']}",
            f"CRS: {layer_info['crs']}",
            f"Source: {layer_info['source']}",
            "",
            f"Columns: {', '.join(layer_info['columns'])}"
        ]
        
        if layer_info['bounds']:
            bounds = layer_info['bounds']
            properties.extend([
                "",
                "Bounds:",
                f"  Min X: {bounds['minx']:.6f}",
                f"  Min Y: {bounds['miny']:.6f}",
                f"  Max X: {bounds['maxx']:.6f}",
                f"  Max Y: {bounds['maxy']:.6f}"
            ])
        
        QMessageBox.information(
            self, 
            f"Layer Properties - {layer_name}",
            "\n".join(properties)
        )
        
    def export_layer(self, layer_name):
        """Export a specific layer"""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            f"Export Layer - {layer_name}",
            f"{layer_name}.geojson",
            "GeoJSON (*.geojson);;Shapefile (*.shp);;CSV (*.csv);;All Files (*)"
        )
        
        if file_path:
            # Determine format from extension
            format_map = {
                '.geojson': 'geojson',
                '.shp': 'shapefile',
                '.csv': 'csv'
            }
            
            file_ext = os.path.splitext(file_path)[1].lower()
            format_type = format_map.get(file_ext, 'geojson')
            
            success = self.data_manager.export_layer(layer_name, file_path, format_type)
            
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Layer '{layer_name}' exported successfully to:\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export layer '{layer_name}'"
                )
                
    def remove_layer(self, layer_name):
        """Remove a specific layer"""
        reply = QMessageBox.question(
            self,
            "Remove Layer",
            f"Are you sure you want to remove layer '{layer_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_manager.remove_layer(layer_name)
            
    def remove_selected_layer(self):
        """Remove the currently selected layer"""
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_name = current_item.data(Qt.UserRole)
            self.remove_layer(layer_name)
            
    def export_selected_layer(self):
        """Export the currently selected layer"""
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_name = current_item.data(Qt.UserRole)
            self.export_layer(layer_name)
