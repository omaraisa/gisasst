#!/usr/bin/env python3
"""
Test script for GIS Copilot Desktop
Verifies that all components are working correctly
"""

import sys
import os
from pathlib import Path

def test_python_packages():
    """Test required Python packages"""
    print("📦 Testing Python packages...")
    
    required_packages = [
        'PyQt5', 'geopandas', 'shapely', 'fiona', 
        'pyproj', 'folium', 'yaml', 'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PyQt5':
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtWebEngineWidgets import QWebEngineView
            elif package == 'yaml':
                import yaml
            elif package == 'dotenv':
                from dotenv import load_dotenv
            else:
                __import__(package.replace('-', '_'))
        except ImportError as e:
            missing_packages.append(f"{package}: {e}")
    
    if missing_packages:
        print(f"❌ Missing packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages installed")
    return True

def test_core_modules():
    """Test core application modules"""
    print("🔧 Testing core modules...")
    
    try:
        # Test imports
        from core.data_manager import DataManager
        from core.ai_agent import AIAgent
        from core.map_manager import MapManager
        from ui.file_browser import FileBrowser
        from ui.chat_panel import ChatPanel
        from ui.layer_panel import LayerPanel
        
        print("✅ Core modules import successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Core module import failed: {e}")
        return False

def test_config_files():
    """Test configuration files"""
    print("📁 Testing configuration files...")
    
    config_path = Path("config/config.yaml")
    env_template_path = Path(".env.template")
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    if not env_template_path.exists():
        print(f"❌ Environment template not found: {env_template_path}")
        return False
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        required_keys = ['ai', 'map', 'ui', 'data']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing configuration section: {key}")
                return False
        
        print("✅ Configuration files OK")
        return True
        
    except Exception as e:
        print(f"❌ Configuration file error: {e}")
        return False

def test_gemini_api():
    """Test Gemini API connection"""
    print("🤖 Testing Gemini API...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("⚠️  Gemini API key not configured")
            print("Please edit .env file and add your API key")
            return False
        
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Simple test
        response = model.generate_content("Say 'test successful' if you can read this.")
        
        if response and response.text:
            print("✅ Gemini API connection OK")
            return True
        else:
            print("❌ Gemini API test failed")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return False

def test_qt_display():
    """Test Qt display capabilities"""
    print("🖥️ Testing Qt display...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        
        # Create a minimal Qt application
        app = QApplication([])
        
        # Test if we can create a web engine view
        web_view = QWebEngineView()
        web_view.setHtml("<html><body><h1>Test</h1></body></html>")
        
        print("✅ Qt display capabilities OK")
        return True
        
    except Exception as e:
        print(f"❌ Qt display error: {e}")
        print("You may need to install additional Qt dependencies")
        return False

def test_spatial_data():
    """Test spatial data handling"""
    print("🗺️ Testing spatial data handling...")
    
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        import pandas as pd
        
        # Create a simple test dataset
        data = {
            'name': ['Point A', 'Point B', 'Point C'],
            'value': [1, 2, 3]
        }
        
        geometry = [Point(46.7, 24.7), Point(46.8, 24.8), Point(46.9, 24.9)]
        gdf = gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326")
        
        # Test basic operations
        buffered = gdf.buffer(0.01)
        bounds = gdf.bounds
        
        if len(gdf) == 3 and not gdf.empty:
            print("✅ Spatial data handling OK")
            return True
        else:
            print("❌ Spatial data test failed")
            return False
            
    except Exception as e:
        print(f"❌ Spatial data error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 GIS Copilot Desktop System Test")
    print("=" * 40)
    
    tests = [
        test_python_packages,
        test_core_modules,
        test_config_files,
        test_spatial_data,
        test_qt_display,
        test_gemini_api
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"🎯 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! GIS Copilot Desktop is ready to use.")
        print("🚀 Run 'python main.py' to start the application")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        if passed >= total - 1:  # Only Gemini API failed
            print("💡 You can still use the application without AI features")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
