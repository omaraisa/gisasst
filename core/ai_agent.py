import google.generativeai as genai
import geopandas as gpd
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
import tempfile
import os
import uuid
from shapely.geometry import Point, LineString, Polygon
import numpy as np

class AIAgent(QObject):
    """AI agent for spatial analysis using Gemini"""
    
    analysis_completed = pyqtSignal(object, str)  # result_gdf, layer_name
    analysis_failed = pyqtSignal(str)  # error_message
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Initialize Gemini
        api_key = config.get('ai', {}).get('api_key') or os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        else:
            self.model = None
            print("Warning: No Gemini API key provided. AI features will be disabled.")
    
    def process_question(self, question, data_manager):
        """Process a spatial analysis question"""
        if not self.model:
            return "AI features are disabled. Please configure your Gemini API key."
        
        try:
            available_layers = data_manager.get_layer_names()
            if not available_layers:
                return "No layers available. Please load some spatial data first."
            
            # Generate analysis code
            code = self._generate_analysis_code(question, available_layers, data_manager)
            
            if code:
                # Execute the analysis
                result = self._execute_analysis(code, data_manager)
                return result
            else:
                return "I couldn't understand your request. Please try rephrasing your question."
                
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            self.analysis_failed.emit(error_msg)
            return error_msg
    
    def _generate_analysis_code(self, question, available_layers, data_manager):
        """Generate Python code for spatial analysis"""
        
        # Get layer information for context
        layer_info = []
        for layer_name in available_layers:
            info = data_manager.get_layer_info(layer_name)
            if info:
                layer_info.append(f"- {layer_name}: {info['geometry_type']}, {info['feature_count']} features, columns: {info['columns']}")
        
        layer_context = "\n".join(layer_info)
        
        prompt = f"""You are an AI assistant for spatial analysis. Generate Python code to answer the user's question.

Available layers:
{layer_context}

Available functions:
- buffer_layer(layer_name, distance_meters) -> returns buffered GeoDataFrame
- select_by_attribute(layer_name, column, value) -> returns filtered GeoDataFrame  
- intersect_layers(layer1_name, layer2_name) -> returns intersection GeoDataFrame
- union_layers(layer1_name, layer2_name) -> returns union GeoDataFrame
- dissolve_layer(layer_name, by_column=None) -> returns dissolved GeoDataFrame
- clip_layer(layer_name, clip_layer_name) -> returns clipped GeoDataFrame
- get_layer_gdf(layer_name) -> returns the GeoDataFrame for a layer

Important rules:
1. Only use the functions listed above
2. Always assign results to 'result_gdf' variable
3. Always assign a descriptive name to 'result_layer_name' variable
4. Don't import any modules
5. Keep it simple and focused
6. Use only layers that exist in the available layers list

User question: {question}

Generate only the Python code, no explanations:"""

        try:
            response = self.model.generate_content(prompt)
            code = response.text.strip()
            
            # Clean the code
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            
            return code.strip()
            
        except Exception as e:
            print(f"Error generating code: {e}")
            return None
    
    def _execute_analysis(self, code, data_manager):
        """Execute the generated analysis code"""
        try:
            # Create execution environment with spatial functions
            execution_env = {
                'buffer_layer': lambda layer_name, distance: self._buffer_layer(layer_name, distance, data_manager),
                'select_by_attribute': lambda layer_name, column, value: self._select_by_attribute(layer_name, column, value, data_manager),
                'intersect_layers': lambda layer1, layer2: self._intersect_layers(layer1, layer2, data_manager),
                'union_layers': lambda layer1, layer2: self._union_layers(layer1, layer2, data_manager),
                'dissolve_layer': lambda layer_name, by_column=None: self._dissolve_layer(layer_name, by_column, data_manager),
                'clip_layer': lambda layer_name, clip_layer: self._clip_layer(layer_name, clip_layer, data_manager),
                'get_layer_gdf': lambda layer_name: data_manager.get_layer(layer_name)['gdf'] if data_manager.get_layer(layer_name) else None,
                'result_gdf': None,
                'result_layer_name': 'analysis_result'
            }
            
            # Execute the code
            exec(code, execution_env)
            
            result_gdf = execution_env.get('result_gdf')
            result_layer_name = execution_env.get('result_layer_name', 'analysis_result')
            
            if result_gdf is not None and not result_gdf.empty:
                # Add the result as a new layer
                final_layer_name = data_manager.add_analysis_result(result_gdf, result_layer_name)
                self.analysis_completed.emit(result_gdf, final_layer_name)
                return f"Analysis completed! Created new layer: '{final_layer_name}' with {len(result_gdf)} features."
            else:
                return "Analysis completed but produced no results."
                
        except Exception as e:
            error_msg = f"Error executing analysis: {str(e)}"
            print(f"Analysis code that failed:\n{code}")
            return error_msg
    
    def _buffer_layer(self, layer_name, distance_meters, data_manager):
        """Create buffer around layer features"""
        layer = data_manager.get_layer(layer_name)
        if not layer:
            raise ValueError(f"Layer '{layer_name}' not found")
        
        gdf = layer['gdf'].copy()
        
        # Convert to projected CRS for accurate buffering (UTM for Middle East)
        original_crs = gdf.crs
        gdf_proj = gdf.to_crs(epsg=32637)  # UTM Zone 37N for Saudi Arabia
        
        # Create buffer
        buffered = gdf_proj.copy()
        buffered['geometry'] = gdf_proj.geometry.buffer(distance_meters)
        
        # Convert back to original CRS
        buffered = buffered.to_crs(original_crs)
        
        return buffered
    
    def _select_by_attribute(self, layer_name, column, value, data_manager):
        """Select features by attribute value"""
        layer = data_manager.get_layer(layer_name)
        if not layer:
            raise ValueError(f"Layer '{layer_name}' not found")
        
        gdf = layer['gdf'].copy()
        
        if column not in gdf.columns:
            raise ValueError(f"Column '{column}' not found in layer '{layer_name}'")
        
        # Handle different value types
        if isinstance(value, str):
            selected = gdf[gdf[column].astype(str).str.contains(value, case=False, na=False)]
        else:
            selected = gdf[gdf[column] == value]
        
        return selected
    
    def _intersect_layers(self, layer1_name, layer2_name, data_manager):
        """Find intersection of two layers"""
        layer1 = data_manager.get_layer(layer1_name)
        layer2 = data_manager.get_layer(layer2_name)
        
        if not layer1:
            raise ValueError(f"Layer '{layer1_name}' not found")
        if not layer2:
            raise ValueError(f"Layer '{layer2_name}' not found")
        
        gdf1 = layer1['gdf'].copy()
        gdf2 = layer2['gdf'].copy()
        
        # Ensure same CRS
        if gdf1.crs != gdf2.crs:
            gdf2 = gdf2.to_crs(gdf1.crs)
        
        # Perform intersection
        intersection = gpd.overlay(gdf1, gdf2, how='intersection')
        
        return intersection
    
    def _union_layers(self, layer1_name, layer2_name, data_manager):
        """Create union of two layers"""
        layer1 = data_manager.get_layer(layer1_name)
        layer2 = data_manager.get_layer(layer2_name)
        
        if not layer1:
            raise ValueError(f"Layer '{layer1_name}' not found")
        if not layer2:
            raise ValueError(f"Layer '{layer2_name}' not found")
        
        gdf1 = layer1['gdf'].copy()
        gdf2 = layer2['gdf'].copy()
        
        # Ensure same CRS
        if gdf1.crs != gdf2.crs:
            gdf2 = gdf2.to_crs(gdf1.crs)
        
        # Perform union
        union = gpd.overlay(gdf1, gdf2, how='union')
        
        return union
    
    def _dissolve_layer(self, layer_name, by_column, data_manager):
        """Dissolve layer features"""
        layer = data_manager.get_layer(layer_name)
        if not layer:
            raise ValueError(f"Layer '{layer_name}' not found")
        
        gdf = layer['gdf'].copy()
        
        if by_column and by_column in gdf.columns:
            dissolved = gdf.dissolve(by=by_column)
        else:
            dissolved = gdf.dissolve()
        
        # Reset index to avoid issues
        dissolved = dissolved.reset_index()
        
        return dissolved
    
    def _clip_layer(self, layer_name, clip_layer_name, data_manager):
        """Clip layer by another layer"""
        layer = data_manager.get_layer(layer_name)
        clip_layer = data_manager.get_layer(clip_layer_name)
        
        if not layer:
            raise ValueError(f"Layer '{layer_name}' not found")
        if not clip_layer:
            raise ValueError(f"Clip layer '{clip_layer_name}' not found")
        
        gdf = layer['gdf'].copy()
        clip_gdf = clip_layer['gdf'].copy()
        
        # Ensure same CRS
        if gdf.crs != clip_gdf.crs:
            clip_gdf = clip_gdf.to_crs(gdf.crs)
        
        # Perform clipping
        clipped = gpd.clip(gdf, clip_gdf)
        
        return clipped
