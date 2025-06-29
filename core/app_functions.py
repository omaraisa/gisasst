"""
Central App Functions Component

This module provides a unified interface for all core application operations.
It can be used by:
1. The main application UI
2. The AI agent for autonomous operations
3. User scripts and automation

All functions are designed to be simple, robust, and AI-friendly.
"""

import os
import tempfile
from pathlib import Path
import geopandas as gpd
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from .logger import get_logger

class AppFunctions:
    """Central hub for all application operations"""
    
    def __init__(self, data_manager, map_manager, main_window=None):
        self.data_manager = data_manager
        self.map_manager = map_manager
        self.main_window = main_window
        self.logger = get_logger(__name__)
        
        # Track operations for undo/redo
        self.operation_history = []
        
    # =============================================================================
    # LAYER MANAGEMENT FUNCTIONS
    # =============================================================================
    
    def load_layer(self, file_path: str, layer_name: str = None) -> Dict[str, Any]:
        """
        Load a spatial layer from file
        
        Args:
            file_path: Path to the spatial file
            layer_name: Optional custom name for the layer
            
        Returns:
            Dict with success status and layer info
        """
        try:
            self.logger.info(f"Loading layer from: {file_path}")
            
            success = self.data_manager.load_file(file_path)
            if success:
                # Get the actual layer name used
                actual_name = Path(file_path).stem if not layer_name else layer_name
                layer_info = self.data_manager.get_layer_info(actual_name)
                
                # Update UI if available
                if self.main_window:
                    self.main_window.refresh_layer_panel()
                    self.main_window.update_map()
                
                result = {
                    'success': True,
                    'layer_name': actual_name,
                    'layer_info': layer_info,
                    'message': f"Successfully loaded layer '{actual_name}'"
                }
                
                self.logger.info(f"Layer loaded successfully: {actual_name}")
                return result
            else:
                return {
                    'success': False,
                    'message': f"Failed to load layer from {file_path}"
                }
                
        except Exception as e:
            error_msg = f"Error loading layer: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def remove_layer(self, layer_name: str) -> Dict[str, Any]:
        """
        Remove a layer from the application
        
        Args:
            layer_name: Name of the layer to remove
            
        Returns:
            Dict with success status and message
        """
        try:
            if layer_name in self.data_manager.layers:
                del self.data_manager.layers[layer_name]
                
                # Update UI if available
                if self.main_window:
                    self.main_window.layer_panel.refresh_layers()
                    self.main_window.update_map()
                
                self.logger.info(f"Layer removed: {layer_name}")
                return {
                    'success': True,
                    'message': f"Layer '{layer_name}' removed successfully"
                }
            else:
                return {
                    'success': False,
                    'message': f"Layer '{layer_name}' not found"
                }
                
        except Exception as e:
            error_msg = f"Error removing layer: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def add_analysis_result(self, gdf: gpd.GeoDataFrame, layer_name: str, 
                          show_on_map: bool = True) -> Dict[str, Any]:
        """
        Add analysis result as a new layer
        
        Args:
            gdf: GeoDataFrame containing the analysis result
            layer_name: Name for the new layer
            show_on_map: Whether to display the layer on the map
            
        Returns:
            Dict with success status and final layer name
        """
        try:
            if gdf is None or gdf.empty:
                return {
                    'success': False,
                    'message': "Cannot add empty or null analysis result"
                }            # Add the layer to data manager
            final_name = self.data_manager.add_analysis_result(gdf, layer_name)
            
            # Update UI if requested and available
            if show_on_map and self.main_window:
                self.main_window.layer_panel.refresh_layers()
                self.main_window.update_map()
            
            self.logger.info(f"Analysis result added as layer: {final_name}")
            return {
                'success': True,
                'layer_name': final_name,
                'feature_count': len(gdf),
                'message': f"Analysis result added as layer '{final_name}' with {len(gdf)} features"
            }
            
        except Exception as e:
            error_msg = f"Error adding analysis result: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def get_layer_info(self, layer_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a layer
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            Dict with layer information or error message
        """
        try:
            if layer_name not in self.data_manager.layers:
                return {
                    'success': False,
                    'message': f"Layer '{layer_name}' not found"
                }
            
            info = self.data_manager.get_layer_info(layer_name)
            layer = self.data_manager.get_layer(layer_name)
            
            result = {
                'success': True,
                'layer_name': layer_name,
                'info': info,
                'gdf': layer['gdf'] if layer else None,
                'visible': layer.get('visible', True) if layer else True
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error getting layer info: {str(e)}"
            }
    
    def list_layers(self) -> Dict[str, Any]:
        """
        Get list of all available layers
        
        Returns:
            Dict with list of layer names and their basic info
        """
        try:
            layer_names = self.data_manager.get_layer_names()
            layers_info = []
            
            for name in layer_names:
                info = self.data_manager.get_layer_info(name)
                if info:
                    layers_info.append({
                        'name': name,
                        'geometry_type': info['geometry_type'],
                        'feature_count': info['feature_count'],
                        'columns': info['columns']
                    })
            
            return {
                'success': True,
                'layers': layers_info,
                'count': len(layers_info)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error listing layers: {str(e)}"
            }
    
    # =============================================================================
    # MAP OPERATIONS
    # =============================================================================
    
    def update_map(self) -> Dict[str, Any]:
        """
        Update the map display with current layers
        
        Returns:
            Dict with success status
        """
        try:
            if self.main_window:
                self.main_window.update_map()
                return {
                    'success': True,
                    'message': "Map updated successfully"
                }
            else:
                return {
                    'success': False,
                    'message': "No main window available for map update"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error updating map: {str(e)}"
            }
    
    def zoom_to_layer(self, layer_name: str) -> Dict[str, Any]:
        """
        Zoom map to a specific layer
        
        Args:
            layer_name: Name of the layer to zoom to
            
        Returns:
            Dict with success status
        """
        try:
            if layer_name not in self.data_manager.layers:
                return {
                    'success': False,
                    'message': f"Layer '{layer_name}' not found"
                }
            
            if self.main_window:
                self.main_window.zoom_to_layer(layer_name)
                return {
                    'success': True,
                    'message': f"Zoomed to layer '{layer_name}'"
                }
            else:
                return {
                    'success': False,
                    'message': "No main window available for zoom operation"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error zooming to layer: {str(e)}"
            }
    
    def toggle_layer_visibility(self, layer_name: str) -> Dict[str, Any]:
        """
        Toggle the visibility of a layer
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            Dict with success status and new visibility state
        """
        try:
            if layer_name not in self.data_manager.layers:
                return {
                    'success': False,
                    'message': f"Layer '{layer_name}' not found"
                }
            
            layer = self.data_manager.layers[layer_name]
            current_visibility = layer.get('visible', True)
            new_visibility = not current_visibility
            layer['visible'] = new_visibility
            
            # Update map
            if self.main_window:
                self.main_window.update_map()
                self.main_window.layer_panel.refresh_layers()
            
            return {
                'success': True,
                'layer_name': layer_name,
                'visible': new_visibility,
                'message': f"Layer '{layer_name}' {'shown' if new_visibility else 'hidden'}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error toggling layer visibility: {str(e)}"
            }
    
    # =============================================================================
    # FILE OPERATIONS
    # =============================================================================
    
    def export_layer(self, layer_name: str, file_path: str, format_type: str = None) -> Dict[str, Any]:
        """
        Export a layer to file
        
        Args:
            layer_name: Name of the layer to export
            file_path: Output file path
            format_type: Optional format (inferred from extension if not provided)
            
        Returns:
            Dict with success status
        """
        try:
            if layer_name not in self.data_manager.layers:
                return {
                    'success': False,
                    'message': f"Layer '{layer_name}' not found"
                }
            
            layer = self.data_manager.get_layer(layer_name)
            gdf = layer['gdf']
            
            # Determine format from extension if not specified
            if not format_type:
                ext = Path(file_path).suffix.lower()
                format_map = {
                    '.shp': 'ESRI Shapefile',
                    '.geojson': 'GeoJSON',
                    '.gpkg': 'GPKG',
                    '.kml': 'KML'
                }
                format_type = format_map.get(ext, 'ESRI Shapefile')
            
            # Export the layer
            gdf.to_file(file_path, driver=format_type)
            
            return {
                'success': True,
                'message': f"Layer '{layer_name}' exported to {file_path}",
                'file_path': file_path,
                'format': format_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error exporting layer: {str(e)}"
            }
    
    def save_map_as_html(self, file_path: str, layers: List[str] = None) -> Dict[str, Any]:
        """
        Save current map as HTML file
        
        Args:
            file_path: Output HTML file path
            layers: Optional list of specific layers to include
            
        Returns:
            Dict with success status
        """
        try:
            # Get layers to include
            if layers:
                layers_dict = {name: self.data_manager.get_layer(name) 
                             for name in layers if name in self.data_manager.layers}
            else:
                layers_dict = self.data_manager.layers
            
            # Export map
            success = self.map_manager.export_map(layers_dict, file_path)
            
            if success:
                return {
                    'success': True,
                    'message': f"Map saved to {file_path}",
                    'file_path': file_path
                }
            else:
                return {
                    'success': False,
                    'message': "Failed to save map"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error saving map: {str(e)}"
            }
    
    # =============================================================================
    # SPATIAL ANALYSIS FUNCTIONS
    # =============================================================================
    
    def buffer_layer(self, layer_name: str, distance: float, unit: str = 'meters') -> Dict[str, Any]:
        """
        Create buffer around layer features
        
        Args:
            layer_name: Name of the source layer
            distance: Buffer distance
            unit: Distance unit (meters, feet, kilometers)
            
        Returns:
            Dict with success status and result layer name
        """
        try:
            if layer_name not in self.data_manager.layers:
                return {
                    'success': False,
                    'message': f"Layer '{layer_name}' not found"
                }
            
            layer = self.data_manager.get_layer(layer_name)
            gdf = layer['gdf'].copy()
            
            # Convert distance to meters if needed
            if unit.lower() in ['km', 'kilometers']:
                distance = distance * 1000
            elif unit.lower() in ['ft', 'feet']:
                distance = distance * 0.3048
            
            # Project to UTM for accurate buffering
            original_crs = gdf.crs
            gdf_proj = gdf.to_crs(epsg=32637)  # UTM Zone 37N for Middle East
            
            # Create buffer
            buffered = gdf_proj.copy()
            buffered['geometry'] = gdf_proj.geometry.buffer(distance)
            
            # Convert back to original CRS
            buffered = buffered.to_crs(original_crs)
            
            # Add as new layer
            result_name = f"{layer_name}_buffer_{distance}m"
            add_result = self.add_analysis_result(buffered, result_name)
            
            if add_result['success']:
                return {
                    'success': True,
                    'result_layer': add_result['layer_name'],
                    'feature_count': len(buffered),
                    'message': f"Buffer created: {add_result['layer_name']}"
                }
            else:
                return add_result
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error creating buffer: {str(e)}"
            }
    
    def intersect_layers(self, layer1_name: str, layer2_name: str) -> Dict[str, Any]:
        """
        Find intersection between two layers
        
        Args:
            layer1_name: Name of first layer
            layer2_name: Name of second layer
            
        Returns:
            Dict with success status and result layer name
        """
        try:
            # Check if layers exist
            for name in [layer1_name, layer2_name]:
                if name not in self.data_manager.layers:
                    return {
                        'success': False,
                        'message': f"Layer '{name}' not found"
                    }
            
            # Get layers
            layer1 = self.data_manager.get_layer(layer1_name)
            layer2 = self.data_manager.get_layer(layer2_name)
            
            gdf1 = layer1['gdf'].copy()
            gdf2 = layer2['gdf'].copy()
            
            # Ensure same CRS
            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)
            
            # Perform intersection
            intersection = gpd.overlay(gdf1, gdf2, how='intersection')
            
            # Add as new layer
            result_name = f"{layer1_name}_intersect_{layer2_name}"
            add_result = self.add_analysis_result(intersection, result_name)
            
            if add_result['success']:
                return {
                    'success': True,
                    'result_layer': add_result['layer_name'],
                    'feature_count': len(intersection),
                    'message': f"Intersection created: {add_result['layer_name']}"
                }
            else:
                return add_result
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error computing intersection: {str(e)}"
            }
    
    def select_by_attribute(self, layer_name: str, column: str, value: Any, 
                          operator: str = 'equals') -> Dict[str, Any]:
        """
        Select features by attribute value
        
        Args:
            layer_name: Name of the source layer
            column: Column name to filter by
            value: Value to filter for
            operator: Comparison operator (equals, contains, greater_than, less_than)
            
        Returns:
            Dict with success status and result layer name
        """
        try:
            if layer_name not in self.data_manager.layers:
                return {
                    'success': False,
                    'message': f"Layer '{layer_name}' not found"
                }
            
            layer = self.data_manager.get_layer(layer_name)
            gdf = layer['gdf'].copy()
            
            if column not in gdf.columns:
                return {
                    'success': False,
                    'message': f"Column '{column}' not found in layer '{layer_name}'"
                }
            
            # Apply filter based on operator
            if operator == 'equals':
                selected = gdf[gdf[column] == value]
            elif operator == 'contains':
                selected = gdf[gdf[column].astype(str).str.contains(str(value), case=False, na=False)]
            elif operator == 'greater_than':
                selected = gdf[gdf[column] > value]
            elif operator == 'less_than':
                selected = gdf[gdf[column] < value]
            else:
                return {
                    'success': False,
                    'message': f"Unknown operator: {operator}"
                }
            
            # Add as new layer
            result_name = f"{layer_name}_selected_{column}_{operator}_{value}"
            add_result = self.add_analysis_result(selected, result_name)
            
            if add_result['success']:
                return {
                    'success': True,
                    'result_layer': add_result['layer_name'],
                    'feature_count': len(selected),
                    'message': f"Selection created: {add_result['layer_name']}"
                }
            else:
                return add_result
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error selecting by attribute: {str(e)}"
            }
    
    # =============================================================================
    # UI OPERATIONS
    # =============================================================================
    
    def refresh_ui(self) -> Dict[str, Any]:
        """
        Refresh all UI components
        
        Returns:
            Dict with success status
        """
        try:
            if self.main_window:
                self.main_window.layer_panel.refresh_layers()
                self.main_window.update_map()
                return {
                    'success': True,
                    'message': "UI refreshed successfully"
                }
            else:
                return {
                    'success': False,
                    'message': "No main window available"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error refreshing UI: {str(e)}"
            }
    
    def show_status_message(self, message: str, timeout: int = 5000) -> Dict[str, Any]:
        """
        Show message in status bar
        
        Args:
            message: Message to display
            timeout: Timeout in milliseconds
            
        Returns:
            Dict with success status
        """
        try:
            if self.main_window and hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage(message, timeout)
                return {
                    'success': True,
                    'message': f"Status message displayed: {message}"
                }
            else:
                self.logger.info(f"Status: {message}")
                return {
                    'success': True,
                    'message': f"Status logged: {message}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error showing status: {str(e)}"
            }
    
    # =============================================================================
    # UTILITY FUNCTIONS
    # =============================================================================
    
    def get_available_functions(self) -> Dict[str, Any]:
        """
        Get list of all available functions for AI agent
        
        Returns:
            Dict with function names and descriptions
        """
        functions = {
            # Layer Management
            'load_layer': 'Load a spatial layer from file',
            'remove_layer': 'Remove a layer from the application',
            'add_analysis_result': 'Add analysis result as a new layer',
            'get_layer_info': 'Get detailed information about a layer',
            'list_layers': 'Get list of all available layers',
            
            # Map Operations
            'update_map': 'Update the map display with current layers',
            'zoom_to_layer': 'Zoom map to a specific layer',
            'toggle_layer_visibility': 'Toggle the visibility of a layer',
            
            # File Operations
            'export_layer': 'Export a layer to file',
            'save_map_as_html': 'Save current map as HTML file',
            
            # Spatial Analysis
            'buffer_layer': 'Create buffer around layer features',
            'intersect_layers': 'Find intersection between two layers',
            'select_by_attribute': 'Select features by attribute value',
            
            # UI Operations
            'refresh_ui': 'Refresh all UI components',
            'show_status_message': 'Show message in status bar'
        }
        
        return {
            'success': True,
            'functions': functions,
            'count': len(functions)
        }
    
    def execute_function(self, function_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a function by name with parameters
        
        Args:
            function_name: Name of the function to execute
            **kwargs: Function parameters
            
        Returns:
            Dict with execution result
        """
        try:
            if hasattr(self, function_name):
                func = getattr(self, function_name)
                result = func(**kwargs)
                
                # Log operation
                self.operation_history.append({
                    'function': function_name,
                    'parameters': kwargs,
                    'result': result,
                    'timestamp': pd.Timestamp.now()
                })
                
                return result
            else:
                return {
                    'success': False,
                    'message': f"Function '{function_name}' not found"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error executing function '{function_name}': {str(e)}"
            }
