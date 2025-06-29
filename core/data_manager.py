import geopandas as gpd
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path
import os
import tempfile
import uuid
from .logger import get_logger

class DataManager(QObject):
    """Manages spatial data layers without requiring a database"""
    
    layer_added = pyqtSignal(str)  # layer_name
    layer_removed = pyqtSignal(str)  # layer_name
    layer_updated = pyqtSignal(str)  # layer_name
    
    def __init__(self):
        super().__init__()
        self.layers = {}  # {layer_name: {'gdf': GeoDataFrame, 'visible': bool, 'style': dict}}
        self.logger = get_logger(__name__)
        
    def load_file(self, file_path):
        """Load a spatial file directly into memory"""
        self.logger.info(f"Attempting to load file: {file_path}")
        try:
            file_path = Path(file_path)
            layer_name = file_path.stem
            
            # Handle duplicate names
            counter = 1
            original_name = layer_name
            while layer_name in self.layers:
                layer_name = f"{original_name}_{counter}"
                counter += 1
            
            self.logger.debug(f"Loading file as layer: {layer_name}")
            
            # Load based on file type
            if file_path.suffix.lower() in ['.shp']:
                gdf = gpd.read_file(str(file_path))
                self.logger.debug(f"Loaded Shapefile with {len(gdf)} features")
            elif file_path.suffix.lower() in ['.geojson', '.json']:
                gdf = gpd.read_file(str(file_path))
                self.logger.debug(f"Loaded GeoJSON with {len(gdf)} features")
            elif file_path.suffix.lower() == '.csv':
                gdf = self._load_csv_with_coordinates(str(file_path))
                self.logger.debug(f"Loaded CSV with {len(gdf)} features")
            elif file_path.suffix.lower() in ['.kml', '.gpx']:
                gdf = gpd.read_file(str(file_path))
                self.logger.debug(f"Loaded {file_path.suffix.upper()} with {len(gdf)} features")
            elif file_path.suffix.lower() == '.gdb' or '.gdb' in str(file_path):
                gdf = self._load_geodatabase(str(file_path))
                self.logger.debug(f"Loaded Geodatabase with {len(gdf)} features")
            else:
                # Try generic spatial file loading
                gdf = gpd.read_file(str(file_path))
                self.logger.debug(f"Loaded generic spatial file with {len(gdf)} features")
            
            # Ensure CRS is set
            if gdf.crs is None:
                gdf.set_crs("EPSG:4326", inplace=True)
                self.logger.warning(f"No CRS found for {layer_name}, defaulting to EPSG:4326")
            else:
                # Reproject to WGS84 for web display
                original_crs = gdf.crs
                gdf = gdf.to_crs("EPSG:4326")
                self.logger.debug(f"Reprojected from {original_crs} to EPSG:4326")
            
            # Add layer
            self.layers[layer_name] = {
                'gdf': gdf,
                'visible': True,
                'style': self._get_default_style(gdf),
                'source_path': str(file_path)
            }
            
            self.logger.info(f"Successfully loaded layer '{layer_name}' with {len(gdf)} features")
            self.layer_added.emit(layer_name)
            return True
            
        except Exception as e:
            self.logger.exception(f"Error loading file {file_path}")
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
        """Load File Geodatabase with improved support"""
        try:
            import fiona
            
            # Check if it's a geodatabase
            if not (file_path.endswith('.gdb') or '.gdb' in file_path):
                raise ValueError("Not a geodatabase file")
            
            # List all layers in the geodatabase
            layers = fiona.listlayers(file_path)
            
            if not layers:
                raise ValueError(f"No layers found in geodatabase: {file_path}")
            
            # For now, load the first layer
            # TODO: In the future, allow user to select which layer to load
            first_layer = layers[0]
            gdf = gpd.read_file(file_path, layer=first_layer)
            
            # Add metadata about available layers
            gdf.attrs = {
                'geodatabase_path': file_path,
                'available_layers': layers,
                'loaded_layer': first_layer
            }
            
            return gdf
            
        except Exception as e:
            # Try alternative approaches
            try:
                # Try reading without specifying layer
                gdf = gpd.read_file(file_path)
                return gdf
            except Exception as e2:
                # Try using GDAL directly if available
                try:
                    try:
                        from osgeo import gdal, ogr
                    except ImportError:
                        # If GDAL is not available, provide helpful error message
                        raise ImportError(
                            "GDAL is required for geodatabase support but not installed. "
                            "Install with: conda install -c conda-forge gdal"
                        )
                    
                    # Open the geodatabase
                    driver = ogr.GetDriverByName("OpenFileGDB")
                    if driver is None:
                        driver = ogr.GetDriverByName("FileGDB")  # Try alternative driver
                    
                    if driver is None:
                        raise ValueError("No suitable GDAL driver found for geodatabase")
                    
                    datasource = driver.Open(file_path, 0)
                    
                    if datasource is None:
                        raise ValueError(f"Could not open geodatabase: {file_path}")
                    
                    # Get first layer
                    layer = datasource.GetLayer(0)
                    if layer is None:
                        raise ValueError("Could not get layer from geodatabase")
                    
                    # Convert to GeoDataFrame
                    features = []
                    for feature in layer:
                        geom = feature.GetGeometryRef()
                        if geom:
                            features.append({
                                'geometry': geom.ExportToWkt(),
                                **{layer.GetLayerDefn().GetFieldDefn(i).GetName(): 
                                   feature.GetField(i) for i in range(feature.GetFieldCount())}
                            })
                    
                    if features:
                        import pandas as pd
                        from shapely import wkt
                        
                        df = pd.DataFrame(features)
                        df['geometry'] = df['geometry'].apply(wkt.loads)
                        gdf = gpd.GeoDataFrame(df, geometry='geometry')
                        
                        # Set CRS if available
                        srs = layer.GetSpatialRef()
                        if srs:
                            gdf.crs = srs.ExportToWkt()
                        
                        return gdf
                    else:
                        raise ValueError("No features found in geodatabase layer")
                        
                except ImportError as ie:
                    raise ValueError(f"Geodatabase support requires GDAL: {str(ie)}")
                except Exception as e3:
                    raise ValueError(f"Failed to load geodatabase with all methods. Errors: {str(e)}, {str(e2)}, {str(e3)}")
    
    def get_geodatabase_layers(self, gdb_path):
        """Get list of layers in a geodatabase"""
        try:
            import fiona
            return fiona.listlayers(gdb_path)
        except Exception:
            try:
                try:
                    from osgeo import ogr
                except ImportError:
                    return []  # GDAL not available
                
                driver = ogr.GetDriverByName("OpenFileGDB")
                if driver is None:
                    driver = ogr.GetDriverByName("FileGDB")
                
                if driver is None:
                    return []
                
                datasource = driver.Open(gdb_path, 0)
                if datasource:
                    return [datasource.GetLayer(i).GetName() for i in range(datasource.GetLayerCount())]
            except Exception:
                pass
        return []
    
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
