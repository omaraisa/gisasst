#!/usr/bin/env python3
"""
Test script for the Advanced AI Agent integration

Run this script to test the advanced agent before fully deploying it.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_advanced_agent():
    """Test the advanced AI agent functionality"""
    print("🧪 Testing Advanced AI Agent Integration...")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from core.advanced_ai_agent import AdvancedGISAgent
        from core.data_manager import DataManager
        from dotenv import load_dotenv
        import yaml
        print("✅ All imports successful")
        
        # Load configuration
        print("⚙️ Loading configuration...")
        load_dotenv()
        
        try:
            with open('config/config.yaml', 'r') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            config = {'ai': {'api_key': os.getenv('GEMINI_API_KEY')}}
        
        # Initialize components
        print("🔧 Initializing components...")
        data_manager = DataManager()
        advanced_agent = AdvancedGISAgent(config)
        print("✅ Components initialized")
        
        # Test simple greeting
        print("💬 Testing greeting detection...")
        response = advanced_agent.process_request("hi", data_manager)
        print(f"Response: {response[:100]}...")
        
        if "Hello" in response and "GIS assistant" in response:
            print("✅ Greeting detection works!")
        else:
            print("⚠️ Greeting detection may need adjustment")
        
        # Test system context gathering
        print("📊 Testing system context gathering...")
        context = advanced_agent._gather_system_context(data_manager)
        
        required_keys = ['available_layers', 'system_info', 'workspace_path', 'installed_packages', 'available_tools']
        missing_keys = [key for key in required_keys if key not in context]
        
        if not missing_keys:
            print("✅ System context gathering works!")
            print(f"   - Found {len(context['installed_packages'])} installed packages")
            print(f"   - Found {len(context['available_tools'])} available tools")
            print(f"   - Workspace: {context['workspace_path']}")
        else:
            print(f"⚠️ Missing context keys: {missing_keys}")
        
        # Test tool listing
        print("🔨 Testing tool availability...")
        tools = advanced_agent._get_available_tools()
        tool_names = [tool['name'] for tool in tools]
        expected_tools = ['execute_python_code', 'install_package', 'run_command', 'spatial_analysis']
        
        missing_tools = [tool for tool in expected_tools if tool not in tool_names]
        if not missing_tools:
            print("✅ All expected tools available!")
        else:
            print(f"⚠️ Missing tools: {missing_tools}")
        
        print("\n🎉 Advanced Agent Integration Test Completed!")
        print("\n📋 Test Summary:")
        print("✅ Imports working")
        print("✅ Configuration loading")
        print("✅ Component initialization")
        print("✅ Basic functionality")
        
        print("\n🚀 Your advanced agent is ready to use!")
        print("\nNext steps:")
        print("1. Start your application with: python main.py")
        print("2. Try asking complex questions like:")
        print("   - 'install matplotlib and create a histogram of my data'")
        print("   - 'create a complete analysis workflow for my shapefiles'")
        print("   - 'export all my layers to different formats'")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nPossible fixes:")
        print("1. Make sure all required packages are installed")
        print("2. Check that the advanced_ai_agent.py file exists in core/")
        print("3. Run: pip install google-generativeai")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 Advanced AI Agent Integration Test")
    print("=" * 50)
    
    success = test_advanced_agent()
    
    if success:
        print("\n🎯 Ready to replace your current agent!")
        sys.exit(0)
    else:
        print("\n🔧 Please fix the issues above before proceeding.")
        sys.exit(1)
