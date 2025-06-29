import folium
import json
import tempfile
from PyQt5.QtCore import QObject
import geopandas as gpd
from .logger import get_logger

class MapManager(QObject):
    """Manages map generation and display"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        
    def generate_map_html(self, layers, center=[24.7135, 46.6753], zoom=10):
        """Generate HTML for map display with all layers"""
        
        self.logger.info(f"Generating map HTML with {len(layers) if layers else 0} layers, center: {center}, zoom: {zoom}")
        
        try:
            # Create base map
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            self.logger.debug("Base map created successfully")
            
            # Add additional tile layers
            folium.TileLayer(
                tiles='Stamen Terrain',
                name='Terrain',
                attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
            ).add_to(m)
            folium.TileLayer(
                tiles='CartoDB positron',
                name='CartoDB Positron',
                attr='© CartoDB © OpenStreetMap contributors'
            ).add_to(m)
            self.logger.debug("Additional tile layers added")
            
            # Add layers
            if layers:
                self.logger.info(f"Adding {len(layers)} layers to map")
                self._add_layers_to_map(m, layers)
                
                # Fit bounds to all visible layers
                self._fit_bounds_to_layers(m, layers)
                self.logger.debug("Map bounds fitted to layers")
            else:
                self.logger.info("No layers to add to map")
            
            # Add layer control
            folium.LayerControl().add_to(m)
            self.logger.debug("Layer control added")
            
            # Add fullscreen plugin
            try:
                from folium.plugins import Fullscreen
                Fullscreen().add_to(m)
                self.logger.debug("Fullscreen plugin added")
            except ImportError as e:
                self.logger.warning(f"Could not add fullscreen plugin: {e}")
            
            # Add measure plugin
            try:
                from folium.plugins import MeasureControl
                MeasureControl().add_to(m)
                self.logger.debug("Measure control plugin added")
            except ImportError as e:
                self.logger.warning(f"Could not add measure control plugin: {e}")
            
            # Return HTML
            html = m._repr_html_()
            self.logger.info("Map HTML generated successfully")
            return html
            
        except Exception as e:
            self.logger.error(f"Error generating map HTML: {e}")
            raise
    
    def _add_layers_to_map(self, folium_map, layers):
        """Add all layers to the folium map"""
        
        self.logger.debug(f"Adding {len(layers)} layers to folium map")
        
        for layer_name, layer_data in layers.items():
            try:
                if not layer_data.get('visible', True):
                    self.logger.debug(f"Skipping layer '{layer_name}' - not visible")
                    continue
                    
                gdf = layer_data['gdf']
                style = layer_data.get('style', {})
                
                if gdf.empty:
                    self.logger.warning(f"Skipping layer '{layer_name}' - empty geodataframe")
                    continue
                
                self.logger.info(f"Adding layer '{layer_name}' with {len(gdf)} features")
                
                # Convert to GeoJSON
                geojson_data = json.loads(gdf.to_json())
                
                # Determine geometry type for styling
                geom_type = gdf.geometry.geom_type.iloc[0] if not gdf.empty else 'Point'
                self.logger.debug(f"Layer '{layer_name}' geometry type: {geom_type}")
                
                if geom_type in ['Point', 'MultiPoint']:
                    self._add_point_layer(folium_map, geojson_data, layer_name, style)
                else:
                    self._add_vector_layer(folium_map, geojson_data, layer_name, style)
                    
                self.logger.debug(f"Successfully added layer '{layer_name}' to map")
                
            except Exception as e:
                self.logger.error(f"Error adding layer '{layer_name}' to map: {e}")
                continue
    
    def _add_point_layer(self, folium_map, geojson_data, layer_name, style):
        """Add point layer to map"""
        
        self.logger.debug(f"Adding point layer '{layer_name}' with {len(geojson_data['features'])} points")
        
        try:
            for feature in geojson_data['features']:
                coords = feature['geometry']['coordinates']
                properties = feature.get('properties', {})
                
                # Create popup content
                popup_content = self._create_popup_content(properties)
                
                folium.CircleMarker(
                    location=[coords[1], coords[0]],  # lat, lon
                    radius=style.get('radius', 5),
                    popup=folium.Popup(popup_content, max_width=300),
                    color=style.get('color', '#3388ff'),
                    fillColor=style.get('fillColor', '#3388ff'),
                    fillOpacity=style.get('fillOpacity', 0.6),
                    weight=style.get('weight', 2)
                ).add_to(folium_map)
                
            self.logger.debug(f"Point layer '{layer_name}' added successfully")
            
        except Exception as e:
            self.logger.error(f"Error adding point layer '{layer_name}': {e}")
            raise
    
    def _add_vector_layer(self, folium_map, geojson_data, layer_name, style):
        """Add vector layer (lines, polygons) to map"""
        
        self.logger.debug(f"Adding vector layer '{layer_name}' with {len(geojson_data['features'])} features")
        
        try:
            def style_function(feature):
                return {
                    'color': style.get('color', '#3388ff'),
                    'weight': style.get('weight', 2),
                    'opacity': style.get('opacity', 0.8),
                    'fillColor': style.get('fillColor', '#3388ff'),
                    'fillOpacity': style.get('fillOpacity', 0.2)
                }
            
            def popup_function(feature):
                properties = feature.get('properties', {})
                return folium.Popup(self._create_popup_content(properties), max_width=300)
            
            folium.GeoJson(
                geojson_data,
                style_function=style_function,
                popup=folium.GeoJsonPopup(
                    fields=list(geojson_data['features'][0]['properties'].keys()) if geojson_data['features'] else [],
                    aliases=list(geojson_data['features'][0]['properties'].keys()) if geojson_data['features'] else [],
                    localize=True,
                    sticky=True,
                    labels=True,
                    style="background-color: white; color: black; font-family: courier new; font-size: 12px; padding: 10px;"
                ),
                tooltip=folium.GeoJsonTooltip(
                    fields=list(geojson_data['features'][0]['properties'].keys())[:3] if geojson_data['features'] else [],
                    aliases=list(geojson_data['features'][0]['properties'].keys())[:3] if geojson_data['features'] else [],
                    localize=True,
                    sticky=True,
                    labels=True,
                    style="background-color: yellow; color: black; font-family: courier new; font-size: 12px; padding: 10px;"
                )
            ).add_to(folium_map)
            
            self.logger.debug(f"Vector layer '{layer_name}' added successfully")
            
        except Exception as e:
            self.logger.error(f"Error adding vector layer '{layer_name}': {e}")
            raise
    
    def _create_popup_content(self, properties):
        """Create popup content from feature properties"""
        if not properties:
            return "No attributes"
        
        content = "<b>Attributes:</b><br>"
        for key, value in properties.items():
            if value is not None and str(value).strip():
                content += f"<b>{key}:</b> {value}<br>"
        
        return content
    
    def _fit_bounds_to_layers(self, folium_map, layers):
        """Fit map bounds to include all visible layers"""
        self.logger.debug("Fitting map bounds to visible layers")
        
        all_bounds = []
        visible_layers = 0
        
        for layer_name, layer_data in layers.items():
            if not layer_data.get('visible', True):
                continue
                
            visible_layers += 1
            gdf = layer_data['gdf']
            if not gdf.empty:
                try:
                    bounds = gdf.bounds
                    if not bounds.empty:
                        # Get overall bounds
                        minx = bounds.minx.min()
                        miny = bounds.miny.min()
                        maxx = bounds.maxx.max()
                        maxy = bounds.maxy.max()
                        all_bounds.extend([[miny, minx], [maxy, maxx]])
                        self.logger.debug(f"Added bounds for layer '{layer_name}': [{miny}, {minx}] to [{maxy}, {maxx}]")
                except Exception as e:
                    self.logger.warning(f"Could not get bounds for layer '{layer_name}': {e}")
        
        self.logger.info(f"Processing bounds for {visible_layers} visible layers")
        
        if all_bounds:
            try:
                # Calculate overall bounds
                min_lat = min(bound[0] for bound in all_bounds)
                min_lon = min(bound[1] for bound in all_bounds)
                max_lat = max(bound[0] for bound in all_bounds)
                max_lon = max(bound[1] for bound in all_bounds)
                
                # Add some padding
                padding = 0.01
                bounds = [
                    [min_lat - padding, min_lon - padding],
                    [max_lat + padding, max_lon + padding]
                ]
                
                self.logger.debug(f"Calculated overall bounds: {bounds}")
                
                try:
                    folium_map.fit_bounds(bounds)
                    self.logger.info(f"Map successfully fitted to bounds: {bounds}")
                except Exception as e:
                    self.logger.warning(f"Failed to fit map to bounds: {e}")
                    pass  # If fitting fails, keep default view
                    
            except Exception as e:
                self.logger.error(f"Error calculating overall bounds: {e}")
        else:
            self.logger.info("No bounds available for fitting - using default view")
    
    def export_map(self, layers, file_path, center=[24.7135, 46.6753], zoom=10):
        """Export map as HTML file"""
        self.logger.info(f"Exporting map to file: {file_path}")
        
        try:
            html_content = self.generate_map_html(layers, center, zoom)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Map successfully exported to: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting map to {file_path}: {e}")
            return False
    
    def get_layer_bounds(self, layer_data):
        """Get bounds for a specific layer"""
        if not layer_data or 'gdf' not in layer_data:
            self.logger.debug("get_layer_bounds: No layer data or gdf not found")
            return None
            
        gdf = layer_data['gdf']
        if gdf.empty:
            self.logger.debug("get_layer_bounds: GeoDataFrame is empty")
            return None
            
        try:
            # Get bounds
            bounds = gdf.bounds
            if bounds.empty:
                self.logger.debug("get_layer_bounds: Bounds are empty")
                return None
                
            # Calculate overall bounds
            minx = bounds.minx.min()
            miny = bounds.miny.min()
            maxx = bounds.maxx.max()
            maxy = bounds.maxy.max()
            
            self.logger.debug(f"Layer bounds: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")
            
            # Add some padding (1% of the range)
            x_range = maxx - minx
            y_range = maxy - miny
            padding_x = x_range * 0.01 if x_range > 0 else 0.001
            padding_y = y_range * 0.01 if y_range > 0 else 0.001
            
            bounds_with_padding = [
                [miny - padding_y, minx - padding_x],  # southwest
                [maxy + padding_y, maxx + padding_x]   # northeast
            ]
            
            self.logger.debug(f"Bounds with padding: {bounds_with_padding}")
            return bounds_with_padding
            
        except Exception as e:
            self.logger.error(f"Error calculating layer bounds: {e}")
            return None
    
    def generate_map_html_zoomed_to_layer(self, layers, zoom_layer_name, default_center=[24.7135, 46.6753], default_zoom=10):
        """Generate HTML for map display zoomed to a specific layer"""
        
        self.logger.info(f"Generating map HTML zoomed to layer '{zoom_layer_name}' with {len(layers) if layers else 0} total layers")
        
        try:
            # Find the layer to zoom to
            zoom_layer_data = None
            if zoom_layer_name in layers:
                zoom_layer_data = layers[zoom_layer_name]
                self.logger.debug(f"Found zoom layer '{zoom_layer_name}'")
            else:
                self.logger.warning(f"Zoom layer '{zoom_layer_name}' not found in available layers")
            
            # Get bounds for zoom layer
            bounds = None
            center = default_center
            zoom = default_zoom
            
            if zoom_layer_data:
                bounds = self.get_layer_bounds(zoom_layer_data)
                if bounds:
                    # Calculate center from bounds
                    center = [
                        (bounds[0][0] + bounds[1][0]) / 2,  # lat
                        (bounds[0][1] + bounds[1][1]) / 2   # lon
                    ]
                    
                    # Calculate appropriate zoom level based on bounds
                    lat_diff = abs(bounds[1][0] - bounds[0][0])
                    lon_diff = abs(bounds[1][1] - bounds[0][1])
                    max_diff = max(lat_diff, lon_diff)
                    
                    # Simple zoom calculation
                    if max_diff > 10:
                        zoom = 6
                    elif max_diff > 1:
                        zoom = 10
                    elif max_diff > 0.1:
                        zoom = 12
                    elif max_diff > 0.01:
                        zoom = 14
                    else:
                        zoom = 16
                    
                    self.logger.info(f"Calculated zoom parameters - center: {center}, zoom: {zoom}, max_diff: {max_diff}")
                else:
                    self.logger.warning(f"Could not get bounds for zoom layer '{zoom_layer_name}', using defaults")
            
            # Create base map
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            self.logger.debug("Base map created for zoomed view")
            
            # Add additional tile layers
            folium.TileLayer(
                tiles='Stamen Terrain',
                name='Terrain',
                attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
            ).add_to(m)
            folium.TileLayer(
                tiles='CartoDB positron',
                name='CartoDB Positron',
                attr='© CartoDB © OpenStreetMap contributors'
            ).add_to(m)
            self.logger.debug("Additional tile layers added to zoomed map")
            
            # Add layers
            if layers:
                self.logger.info(f"Adding {len(layers)} layers to zoomed map")
                self._add_layers_to_map(m, layers)
                
                # If we have specific bounds, fit to them
                if bounds:
                    try:
                        m.fit_bounds(bounds)
                        self.logger.debug(f"Map fitted to bounds: {bounds}")
                    except Exception as e:
                        self.logger.warning(f"Failed to fit map to bounds: {e}")
                        pass  # If fitting fails, keep calculated center and zoom
            else:
                self.logger.info("No layers to add to zoomed map")
            
            # Add layer control
            folium.LayerControl().add_to(m)
            self.logger.debug("Layer control added to zoomed map")
            
            # Add fullscreen plugin
            try:
                from folium.plugins import Fullscreen
                Fullscreen().add_to(m)
                self.logger.debug("Fullscreen plugin added to zoomed map")
            except ImportError as e:
                self.logger.warning(f"Could not add fullscreen plugin to zoomed map: {e}")
            
            # Add measure plugin
            try:
                from folium.plugins import MeasureControl
                MeasureControl().add_to(m)
                self.logger.debug("Measure control plugin added to zoomed map")
            except ImportError as e:
                self.logger.warning(f"Could not add measure control plugin to zoomed map: {e}")
            
            # Return HTML
            html = m._repr_html_()
            self.logger.info(f"Zoomed map HTML generated successfully for layer '{zoom_layer_name}'")
            return html
            
        except Exception as e:
            self.logger.error(f"Error generating zoomed map HTML for layer '{zoom_layer_name}': {e}")
            raise
