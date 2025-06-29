"""
Test script to verify AppFunctions integration with the AI agent.
This script tests that the AI agent can properly add analysis results to the map.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import tempfile

from core.data_manager import DataManager
from core.map_manager import MapManager
from core.app_functions import AppFunctions
from core.advanced_ai_agent import AdvancedGISAgent
from core.logger import setup_logging, get_logger

def create_test_data():
    """Create some test geographic data"""
    print("Creating test data...")
    
    # Create test points
    points_data = {
        'name': ['Point A', 'Point B', 'Point C', 'Point D'],
        'value': [10, 20, 30, 40],
        'geometry': [
            Point(31.2357, 30.0444),  # Cairo
            Point(31.2357, 30.1444),  # North of Cairo
            Point(31.3357, 30.0444),  # East of Cairo  
            Point(31.1357, 30.0444),  # West of Cairo
        ]
    }
    points_gdf = gpd.GeoDataFrame(points_data, crs='EPSG:4326')
    
    # Create test polygon
    polygon_coords = [
        (31.2, 30.0),
        (31.3, 30.0), 
        (31.3, 30.1),
        (31.2, 30.1),
        (31.2, 30.0)
    ]
    polygon_data = {
        'name': ['Test Area'],
        'area_type': ['Study Area'],
        'geometry': [Polygon(polygon_coords)]
    }
    polygon_gdf = gpd.GeoDataFrame(polygon_data, crs='EPSG:4326')
    
    return points_gdf, polygon_gdf

def test_app_functions_integration():
    """Test that AppFunctions properly integrates with the AI agent"""
    print("Testing AppFunctions integration...")
    
    # Setup logging
    logger, _ = setup_logging(log_level='INFO', log_to_console=True)
    
    try:
        # Initialize components
        data_manager = DataManager()
        map_manager = MapManager()
        
        # Initialize app functions
        app_functions = AppFunctions(
            data_manager=data_manager,
            map_manager=map_manager,
            main_window=None  # No UI for this test
        )
        
        # Create test config
        config = {
            'ai': {
                'api_key': os.getenv('GEMINI_API_KEY', 'test_key')
            }
        }
        
        # Initialize AI agent with app functions
        ai_agent = AdvancedGISAgent(config, app_functions)
        
        # Create test data
        points_gdf, polygon_gdf = create_test_data()
        
        # Test 1: Add analysis results using app_functions
        print("\nTest 1: Adding analysis results...")
        
        result1 = app_functions.add_analysis_result(points_gdf, "test_points")
        print(f"Add points result: {result1}")
        
        result2 = app_functions.add_analysis_result(polygon_gdf, "test_polygon") 
        print(f"Add polygon result: {result2}")
        
        # Test 2: Check that layers were added
        print("\nTest 2: Checking layers...")
        layers = app_functions.list_layers()
        print(f"Available layers: {layers}")
        
        # Test 3: Test buffer operation
        print("\nTest 3: Testing buffer operation...")
        buffer_result = app_functions.buffer_layer("test_points", 1000, "meters")
        print(f"Buffer result: {buffer_result}")
        
        # Test 4: Test the AI agent's Python code execution with app_functions
        print("\nTest 4: Testing AI agent code execution...")
        
        test_code = """
# Test code for AI agent with app_functions
print("Testing AI agent access to app_functions...")

# Get available layers
if app_functions:
    layers = app_functions.list_layers()
    print(f"Available layers via app_functions: {layers['layers']}")
    
    # Create a simple analysis result
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Create a test point
    test_point = gpd.GeoDataFrame({
        'name': ['AI Created Point'],
        'source': ['AI Agent'],
        'geometry': [Point(31.25, 30.05)]
    }, crs='EPSG:4326')
    
    # Add it using app_functions
    add_result = app_functions.add_analysis_result(test_point, 'ai_test_point')
    print(f"AI agent add result: {add_result}")
    
    result = f"AI agent successfully created and added layer: {add_result.get('layer_name', 'unknown')}"
else:
    result = "app_functions not available"
"""
        
        # Execute the test code
        execution_result = ai_agent._execute_python_code(test_code, data_manager)
        print(f"Code execution result: {execution_result}")
        
        # Test 5: Final layer check
        print("\nTest 5: Final layer check...")
        final_layers = app_functions.list_layers()
        print(f"Final layers: {final_layers}")
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("AppFunctions Integration Test")
    print("=" * 40)
    
    success = test_app_functions_integration()
    
    if success:
        print("\n🎉 Integration test PASSED!")
        print("The AI agent can now easily add analysis results to the map using AppFunctions.")
    else:
        print("\n💥 Integration test FAILED!")
        print("Check the error messages above for debugging information.")
    
    sys.exit(0 if success else 1)
