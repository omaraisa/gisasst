"""
Integration example for the Advanced GIS Agent

This shows how to integrate the new tool-based agent with your existing system.
"""

from core.advanced_ai_agent import AdvancedGISAgent
from core.ai_agent import AIAgent  # Your existing agent

class HybridGISAgent:
    """Hybrid agent that can use both simple and advanced modes"""
    
    def __init__(self, config):
        self.simple_agent = AIAgent(config)
        self.advanced_agent = AdvancedGISAgent(config)
        self.mode = "auto"  # "simple", "advanced", or "auto"
    
    def process_request(self, user_request, data_manager):
        """Route requests to appropriate agent based on complexity"""
        
        # Determine complexity
        if self._is_complex_request(user_request):
            print("🚀 Using Advanced Agent (autonomous mode)")
            return self.advanced_agent.process_request(user_request, data_manager)
        else:
            print("⚡ Using Simple Agent (function-based mode)")
            return self.simple_agent.process_question(user_request, data_manager)
    
    def _is_complex_request(self, request):
        """Determine if request needs advanced agent"""
        complex_indicators = [
            "install", "download", "scrape", "web", "api", "multiple steps",
            "first", "then", "after that", "combine", "workflow", "pipeline",
            "automate", "script", "command", "system", "file", "export",
            "import", "convert", "transform", "clean", "prepare"
        ]
        
        request_lower = request.lower()
        return any(indicator in request_lower for indicator in complex_indicators)

# Usage example in your main application:
"""
# In your chat panel or main app:

hybrid_agent = HybridGISAgent(config)

def on_user_message(message):
    response = hybrid_agent.process_request(message, data_manager)
    display_response(response)

# Example requests that would use different agents:

# Simple Agent:
"buffer roads by 500 meters"
"find places near railways"
"hi"

# Advanced Agent:
"install plotly and create an interactive 3D visualization of my elevation data"
"download weather data from NOAA API and correlate it with my agricultural zones"
"create a complete workflow to process new shapefiles: clean data, validate geometry, and generate summary reports"
"export all my layers to different formats and upload them to my cloud storage"
"""
