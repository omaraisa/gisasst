import folium
import json
import tempfile
from PyQt5.QtCore import QObject
import geopandas as gpd

class MapManager(QObject):
    """Manages map generation and display"""
    
    def __init__(self):
        super().__init__()
        
    def generate_map_html(self, layers, center=[24.7135, 46.6753], zoom=10):
        """Generate HTML for map display with all layers"""
        
        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Add additional tile layers
        folium.TileLayer('Stamen Terrain', name='Terrain').add_to(m)
        folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(m)
        
        # Add layers
        if layers:
            self._add_layers_to_map(m, layers)
            
            # Fit bounds to all visible layers
            self._fit_bounds_to_layers(m, layers)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add fullscreen plugin
        from folium.plugins import Fullscreen
        Fullscreen().add_to(m)
        
        # Add measure plugin
        try:
            from folium.plugins import MeasureControl
            MeasureControl().add_to(m)
        except:
            pass  # If plugin not available
        
        # Return HTML
        return m._repr_html_()
    
    def _add_layers_to_map(self, folium_map, layers):
        """Add all layers to the folium map"""
        
        for layer_name, layer_data in layers.items():
            if not layer_data.get('visible', True):
                continue
                
            gdf = layer_data['gdf']
            style = layer_data.get('style', {})
            
            if gdf.empty:
                continue
            
            # Convert to GeoJSON
            geojson_data = json.loads(gdf.to_json())
            
            # Determine geometry type for styling
            geom_type = gdf.geometry.geom_type.iloc[0] if not gdf.empty else 'Point'
            
            if geom_type in ['Point', 'MultiPoint']:
                self._add_point_layer(folium_map, geojson_data, layer_name, style)
            else:
                self._add_vector_layer(folium_map, geojson_data, layer_name, style)
    
    def _add_point_layer(self, folium_map, geojson_data, layer_name, style):
        """Add point layer to map"""
        
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
    
    def _add_vector_layer(self, folium_map, geojson_data, layer_name, style):
        """Add vector layer (lines, polygons) to map"""
        
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
        all_bounds = []
        
        for layer_name, layer_data in layers.items():
            if not layer_data.get('visible', True):
                continue
                
            gdf = layer_data['gdf']
            if not gdf.empty:
                bounds = gdf.bounds
                if not bounds.empty:
                    # Get overall bounds
                    minx = bounds.minx.min()
                    miny = bounds.miny.min()
                    maxx = bounds.maxx.max()
                    maxy = bounds.maxy.max()
                    all_bounds.extend([[miny, minx], [maxy, maxx]])
        
        if all_bounds:
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
            
            try:
                folium_map.fit_bounds(bounds)
            except:
                pass  # If fitting fails, keep default view
    
    def export_map(self, layers, file_path, center=[24.7135, 46.6753], zoom=10):
        """Export map as HTML file"""
        try:
            html_content = self.generate_map_html(layers, center, zoom)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except Exception as e:
            print(f"Error exporting map: {e}")
            return False
