"""Configuration manager for GIS Copilot Desktop."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration from YAML files and environment variables."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        self._config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and environment variables."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        else:
            # Default configuration if file doesn't exist
            self._config = {
                "ai": {
                    "model": "gemini-2.5-flash-latest",
                    "api_key": ""
                },
                "map": {
                    "default_center": [24.7135, 46.6753],  # Riyadh
                    "default_zoom": 10
                },
                "ui": {
                    "theme": "dark"
                },
                "data": {
                    "temp_directory": "temp",
                    "supported_formats": [".shp", ".geojson", ".json", ".csv", ".kml", ".gpx", ".gdb"]
                }
            }
        
        # Override with environment variables
        if os.getenv("GEMINI_API_KEY"):
            self._config["ai"]["api_key"] = os.getenv("GEMINI_API_KEY")
        
        if os.getenv("THEME"):
            self._config["ui"]["theme"] = os.getenv("THEME")
        
        return self._config
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        if self._config is None:
            self.load_config()
        return self._config
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI-specific configuration."""
        return self.get_config().get("ai", {})
    
    def get_map_config(self) -> Dict[str, Any]:
        """Get map-specific configuration."""
        return self.get_config().get("map", {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI-specific configuration."""
        return self.get_config().get("ui", {})
    
    def get_data_config(self) -> Dict[str, Any]:
        """Get data-specific configuration."""
        return self.get_config().get("data", {})
    
    def get_api_key(self) -> str:
        """Get the Gemini API key."""
        return self.get_ai_config().get("api_key", "")
    
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        api_key = self.get_api_key()
        return bool(api_key and api_key.strip())
