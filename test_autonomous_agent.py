#!/usr/bin/env python3
"""
Test script for the Autonomous GIS Agent

This script tests the agent's capabilities without the full UI.
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Add core to path
sys.path.append(str(Path(__file__).parent / "core"))

from core.autonomous_gis_agent import AutonomousGISAgent
from core.data_manager import DataManager
from core.app_functions import AppFunctions
from core.map_manager import MapManager

def load_config():
    """Load configuration"""
    load_dotenv()
    config_path = Path(__file__).parent / "config" / "config.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        return {
            'ai': {
                'api_key': os.getenv('GEMINI_API_KEY')
            }
        }

def test_autonomous_agent():
    """Test the autonomous agent"""
    print("🚀 Testing Autonomous GIS Agent...")
    
    # Load config
    config = load_config()
    
    # Initialize components
    data_manager = DataManager()
    map_manager = MapManager()
    app_functions = AppFunctions(
        data_manager=data_manager,
        map_manager=map_manager,
        main_window=None
    )
    
    # Initialize autonomous agent
    agent = AutonomousGISAgent(
        config=config,
        app_functions=app_functions,
        data_manager=data_manager
    )
    
    # Connect signals for testing
    def on_thinking_started(message):
        print(f"🧠 {message}")
    
    def on_plan_created(plan):
        print(f"📋 Plan: {plan.goal}")
        print(f"📝 Approach: {plan.approach}")
        print(f"🔢 Steps: {len(plan.steps)}")
    
    def on_step_started(step_id, description):
        print(f"⚙️ {step_id}: {description}")
    
    def on_step_completed(step_id, result):
        print(f"✅ {step_id}: Completed")
    
    def on_step_failed(step_id, error):
        print(f"❌ {step_id}: {error}")
    
    def on_plan_completed(final_response):
        print(f"🎯 Final: {final_response}")
    
    def on_conversation_response(response):
        print(f"💬 Conversation: {response}")
    
    # Connect signals
    agent.thinking_started.connect(on_thinking_started)
    agent.plan_created.connect(on_plan_created)
    agent.step_started.connect(on_step_started)
    agent.step_completed.connect(on_step_completed)
    agent.step_failed.connect(on_step_failed)
    agent.plan_completed.connect(on_plan_completed)
    agent.conversation_response.connect(on_conversation_response)
    
    # Add some sample data for testing
    print("📊 Adding sample data for testing...")
    try:
        import geopandas as gpd
        from shapely.geometry import Point, LineString
        import pandas as pd
        
        # Create sample points (cities)
        cities_data = {
            'name': ['Riyadh', 'Jeddah', 'Dammam'],
            'geometry': [Point(46.6753, 24.7135), Point(39.1612, 21.4858), Point(50.0888, 26.4282)]
        }
        cities_gdf = gpd.GeoDataFrame(cities_data, crs='EPSG:4326')
        data_manager.add_layer(cities_gdf, 'cities')
        
        # Create sample roads (lines)
        roads_data = {
            'name': ['Highway 1', 'Highway 2'],
            'geometry': [
                LineString([(46.5, 24.5), (46.8, 24.9)]),
                LineString([(46.6, 24.6), (46.7, 24.8)])
            ]
        }
        roads_gdf = gpd.GeoDataFrame(roads_data, crs='EPSG:4326')
        data_manager.add_layer(roads_gdf, 'roads')
        
        print(f"✅ Added sample data: {data_manager.get_layer_names()}")
        
    except Exception as e:
        print(f"⚠️ Could not add sample data: {e}")
    
    # Test conversations and tasks
    test_inputs = [
        "Hi there!",
        "What is GIS?", 
        "What layers do I have available?",
        "How do buffers work in spatial analysis?",
        "Load some sample data for testing",
        "Create a buffer around roads",
        "Tell me about spatial relationships"
    ]
    
    for test_input in test_inputs:
        print(f"\n{'='*50}")
        print(f"USER: {test_input}")
        print("-" * 50)
        
        try:
            response = agent.process_input(test_input)
            print(f"RESPONSE: {response}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_autonomous_agent()
