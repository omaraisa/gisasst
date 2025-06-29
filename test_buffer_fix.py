#!/usr/bin/env python3
"""
Test Buffer Fix
===============

Test script to verify that the AI agent can properly access existing layers
and perform buffer operations without trying to read files.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.advanced_ai_agent import AdvancedGISAgent
from core.data_manager import DataManager
from core.app_functions import AppFunctions
from core.logger import setup_logging
import yaml
import geopandas as gpd
from shapely.geometry import Point

def test_buffer_fix():
    """Test that buffer operations work with existing layers"""
    print("Buffer Fix Test")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create components
    data_manager = DataManager()
    app_functions = AppFunctions(data_manager, None)
    agent = AdvancedGISAgent(config, app_functions)
    
    print("\nStep 1: Creating test layer...")
    # Create test points layer (simulating loaded data)
    test_points = gpd.GeoDataFrame({
        'name': ['Cairo', 'Alexandria', 'Giza'],
        'type': ['capital', 'port', 'historic'],
        'geometry': [
            Point(31.2357, 30.0444),  # Cairo
            Point(29.9187, 31.2001),  # Alexandria
            Point(31.2089, 30.0131)   # Giza
        ]
    }, crs='EPSG:4326')
    
    # Add to data manager (simulating loaded layer)
    data_manager.layers['cities'] = {
        'gdf': test_points,
        'source': 'test_data',
        'visible': True
    }
    
    print(f"✅ Created test layer 'cities' with {len(test_points)} features")
    print(f"Available layers: {data_manager.get_layer_names()}")
    
    print("\nStep 2: Testing layer access functions...")
    # Test the execution environment functions
    execution_env = {
        'get_layer': lambda name: data_manager.get_layer(name)['gdf'] if name in data_manager.layers else None,
        'get_layer_names': lambda: data_manager.get_layer_names(),
        'buffer_layer': lambda layer_name, distance, unit='meters': app_functions.buffer_layer(layer_name, distance, unit),
        'print': print,
        'len': len,
    }
    
    # Test code that should work
    test_code = """
print("Testing layer access...")
layer_names = get_layer_names()
print(f"Available layers: {layer_names}")

if 'cities' in layer_names:
    cities_data = get_layer('cities')
    print(f"Cities layer has {len(cities_data)} features")
    print(f"Columns: {list(cities_data.columns)}")
    
    # Test buffer operation
    print("Testing buffer operation...")
    buffer_result = buffer_layer('cities', 1000, 'meters')
    print(f"Buffer result: {buffer_result}")
else:
    print("Cities layer not found!")
"""
    
    try:
        exec(test_code, execution_env)
        print("✅ Layer access test completed successfully!")
    except Exception as e:
        print(f"❌ Layer access test failed: {e}")
    
    print("\nStep 3: Testing AI agent context...")
    # Test that the AI gets the right context
    context = agent._gather_system_context(data_manager)
    print(f"Available layers in context: {[layer['name'] for layer in context['available_layers']]}")
    
    print("\nStep 4: Testing execution environment...")
    # Test the actual execution environment
    exec_env = {
        'get_layer': lambda name: data_manager.get_layer(name)['gdf'] if name in data_manager.layers else None,
        'buffer_layer': lambda layer_name, distance, unit='meters': app_functions.buffer_layer(layer_name, distance, unit),
        'print': print,
        'len': len,
    }
    
    simple_buffer_code = """
print("Executing buffer operation...")
layer_data = get_layer('cities')
print(f"Got layer with {len(layer_data)} features")

result = buffer_layer('cities', 1000, 'meters')
print(f"Buffer operation result: {result}")
"""
    
    try:
        exec(simple_buffer_code, exec_env)
        print("✅ Buffer operation test completed successfully!")
    except Exception as e:
        print(f"❌ Buffer operation test failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Buffer fix tests completed!")
    print("\nThe AI should now:")
    print("1. Use get_layer() instead of reading files")
    print("2. Use buffer_layer() app function")
    print("3. Automatically add results to map")

if __name__ == "__main__":
    test_buffer_fix()
