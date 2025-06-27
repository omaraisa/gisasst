import geopandas as gpd
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path
import os
import tempfile
import uuid

class DataManager(QObject):
    """Manages spatial data layers without requiring a database"""
    
    layer_added = pyqtSignal(str)  # layer_name
    layer_removed = pyqtSignal(str)  # layer_name
    layer_updated = pyqtSignal(str)  # layer_name
    
    def __init__(self):
        super().__init__()
        self.layers = {}  # {layer_name: {'gdf': GeoDataFrame, 'visible': bool, 'style': dict}}
        
    def load_file(self, file_path):
        """Load a spatial file directly into memory"""
        try:
            file_path = Path(file_path)
            layer_name = file_path.stem
            
            # Handle duplicate names
            counter = 1
            original_name = layer_name
            while layer_name in self.layers:
                layer_name = f"{original_name}_{counter}"
                counter += 1
            
            # Load based on file type
            if file_path.suffix.lower() in ['.shp']:
                gdf = gpd.read_file(str(file_path))
            elif file_path.suffix.lower() in ['.geojson', '.json']:
                gdf = gpd.read_file(str(file_path))
            elif file_path.suffix.lower() == '.csv':
                gdf = self._load_csv_with_coordinates(str(file_path))
            elif file_path.suffix.lower() in ['.kml', '.gpx']:
                gdf = gpd.read_file(str(file_path))
            elif file_path.suffix.lower() == '.gdb' or '.gdb' in str(file_path):
                gdf = self._load_geodatabase(str(file_path))
            else:
                # Try generic spatial file loading
                gdf = gpd.read_file(str(file_path))
            
            # Ensure CRS is set
            if gdf.crs is None:
                gdf.set_crs("EPSG:4326", inplace=True)
            else:
                # Reproject to WGS84 for web display
                gdf = gdf.to_crs("EPSG:4326")
            
            # Add layer
            self.layers[layer_name] = {
                'gdf': gdf,
                'visible': True,
                'style': self._get_default_style(gdf),
                'source_path': str(file_path)
            }
            
            self.layer_added.emit(layer_name)
            return True
            
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return False
    
    def _load_csv_with_coordinates(self, file_path):
        """Load CSV file with coordinate columns"""
        df = pd.read_csv(file_path)
        
        # Try different common column names for coordinates
        lon_cols = ['longitude', 'lon', 'lng', 'x', 'X', 'long']
        lat_cols = ['latitude', 'lat', 'y', 'Y']
        
        lon_col = None
        lat_col = None
        
        for col in lon_cols:
            if col in df.columns:
                lon_col = col
                break
        
        for col in lat_cols:
            if col in df.columns:
                lat_col = col
                break
        
        if lon_col and lat_col:
            gdf = gpd.GeoDataFrame(
                df, 
                geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), 
                crs="EPSG:4326"
            )
            return gdf
        else:
            raise ValueError(f"CSV file must contain coordinate columns. Found columns: {list(df.columns)}")
    
    def _load_geodatabase(self, file_path):
        """Load File Geodatabase"""
        try:
            import fiona
            layers = fiona.listlayers(file_path)
            if layers:
                # Read the first layer
                gdf = gpd.read_file(file_path, layer=layers[0])
                return gdf
            else:
                raise ValueError(f"No layers found in geodatabase: {file_path}")
        except Exception as e:
            # Fallback: try reading without specifying layer
            gdf = gpd.read_file(file_path)
            return gdf
    
    def _get_default_style(self, gdf):
        """Get default styling based on geometry type"""
        geom_type = gdf.geometry.geom_type.iloc[0] if not gdf.empty else 'Point'
        
        if geom_type in ['Point', 'MultiPoint']:
            return {
                'color': '#3388ff',
                'fillColor': '#3388ff',
                'fillOpacity': 0.6,
                'radius': 5,
                'weight': 2
            }
        elif geom_type in ['LineString', 'MultiLineString']:
            return {
                'color': '#3388ff',
                'weight': 3,
                'opacity': 0.8
            }
        else:  # Polygon, MultiPolygon
            return {
                'color': '#3388ff',
                'fillColor': '#3388ff',
                'fillOpacity': 0.2,
                'weight': 2,
                'opacity': 0.8
            }
    
    def remove_layer(self, layer_name):
        """Remove a layer"""
        if layer_name in self.layers:
            del self.layers[layer_name]
            self.layer_removed.emit(layer_name)
            return True
        return False
    
    def get_layer(self, layer_name):
        """Get layer data"""
        return self.layers.get(layer_name)
    
    def get_layers(self):
        """Get all layers"""
        return self.layers
    
    def get_layer_names(self):
        """Get list of layer names"""
        return list(self.layers.keys())
    
    def set_layer_visibility(self, layer_name, visible):
        """Set layer visibility"""
        if layer_name in self.layers:
            self.layers[layer_name]['visible'] = visible
            self.layer_updated.emit(layer_name)
    
    def is_layer_visible(self, layer_name):
        """Check if layer is visible"""
        layer = self.layers.get(layer_name)
        return layer['visible'] if layer else False
    
    def add_analysis_result(self, result_gdf, layer_name):
        """Add analysis result as a new layer"""
        # Handle duplicate names
        counter = 1
        original_name = layer_name
        while layer_name in self.layers:
            layer_name = f"{original_name}_{counter}"
            counter += 1
        
        # Ensure CRS
        if result_gdf.crs is None:
            result_gdf.set_crs("EPSG:4326", inplace=True)
        else:
            result_gdf = result_gdf.to_crs("EPSG:4326")
        
        self.layers[layer_name] = {
            'gdf': result_gdf,
            'visible': True,
            'style': self._get_default_style(result_gdf),
            'source_path': 'analysis_result'
        }
        
        self.layer_added.emit(layer_name)
        return layer_name
    
    def export_layer(self, layer_name, file_path, format='geojson'):
        """Export layer to file"""
        if layer_name not in self.layers:
            return False
        
        try:
            gdf = self.layers[layer_name]['gdf']
            
            if format.lower() == 'geojson':
                gdf.to_file(file_path, driver='GeoJSON')
            elif format.lower() == 'shapefile':
                gdf.to_file(file_path, driver='ESRI Shapefile')
            elif format.lower() == 'csv':
                # Convert to regular DataFrame with lat/lon columns
                df = gdf.copy()
                df['longitude'] = gdf.geometry.x
                df['latitude'] = gdf.geometry.y
                df = df.drop('geometry', axis=1)
                df.to_csv(file_path, index=False)
            else:
                gdf.to_file(file_path)
            
            return True
        except Exception as e:
            print(f"Error exporting layer {layer_name}: {e}")
            return False
    
    def get_layer_info(self, layer_name):
        """Get information about a layer"""
        if layer_name not in self.layers:
            return None
        
        gdf = self.layers[layer_name]['gdf']
        
        return {
            'name': layer_name,
            'geometry_type': gdf.geometry.geom_type.iloc[0] if not gdf.empty else 'Unknown',
            'feature_count': len(gdf),
            'crs': str(gdf.crs),
            'bounds': gdf.bounds.iloc[0].to_dict() if not gdf.empty else None,
            'columns': list(gdf.columns),
            'visible': self.layers[layer_name]['visible'],
            'source': self.layers[layer_name].get('source_path', 'Unknown')
        }
