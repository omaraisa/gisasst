#!/usr/bin/env python3
"""
Test Simple Request Handling
=============================

Test script to verify that the AI agent can handle simple requests
directly without going through complex AI planning.
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
from shapely.geometry import Point, Polygon

def test_simple_requests():
    """Test simple request handling"""
    print("Simple Request Handler Test")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create components
    data_manager = DataManager()
    app_functions = AppFunctions(data_manager, None, None)
    agent = AdvancedGISAgent(config, app_functions)
    
    print("\nTest 1: List layers (empty)")
    result1 = agent._handle_simple_requests('list layer names', data_manager)
    print(f"Result: {result1}")
    
    print("\nTest 2: Adding test data...")
    # Create test points
    test_points = gpd.GeoDataFrame({
        'name': ['Cairo', 'Alexandria', 'Giza'],
        'population': [9000000, 4500000, 3500000],
        'geometry': [Point(31.2357, 30.0444), Point(29.9187, 31.2001), Point(31.2089, 30.0131)]
    }, crs='EPSG:4326')
    
    # Create test polygon
    test_polygon = gpd.GeoDataFrame({
        'name': ['Egypt Border'],
        'area_type': ['country'],
        'geometry': [Polygon([(25, 22), (36, 22), (36, 32), (25, 32), (25, 22)])]
    }, crs='EPSG:4326')
    
    # Add to data manager
    data_manager.add_analysis_result(test_points, 'cities')
    data_manager.add_analysis_result(test_polygon, 'borders')
    
    print("\nTest 3: List layers (with data)")
    result2 = agent._handle_simple_requests('list layers', data_manager)
    print(f"Result: {result2}")
    
    print("\nTest 4: Show available layers")
    result3 = agent._handle_simple_requests('show layer names', data_manager)
    print(f"Result: {result3}")
    
    print("\nTest 5: What layers are available")
    result4 = agent._handle_simple_requests('what layers are available', data_manager)
    print(f"Result: {result4}")
    
    print("\nTest 6: Help request")
    result5 = agent._handle_simple_requests('help', data_manager)
    print(f"Result: {result5}")
    
    print("\nTest 7: Layer info request")
    result6 = agent._handle_simple_requests('layer info cities', data_manager)
    print(f"Result: {result6}")
    
    print("\nTest 8: Update map request")
    result7 = agent._handle_simple_requests('update map', data_manager)
    print(f"Result: {result7}")
    
    print("\nTest 9: Non-simple request (should return None)")
    result8 = agent._handle_simple_requests('create a buffer around cities', data_manager)
    print(f"Result: {result8}")
    
    print("\n" + "=" * 50)
    print("✅ Simple request handler tests completed!")

if __name__ == "__main__":
    test_simple_requests()
