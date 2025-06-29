import google.generativeai as genai
import geopandas as gpd
import pandas as pd
import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from .logger import get_logger

class AdvancedGISAgent(QObject):
    """Advanced autonomous GIS agent with tool-based architecture"""
    
    analysis_completed = pyqtSignal(object, str)
    analysis_failed = pyqtSignal(str)
    status_update = pyqtSignal(str)  # For reporting progress
    
    def __init__(self, config, app_functions=None):
        super().__init__()
        self.config = config
        self.app_functions = app_functions  # Central hub for all operations
        self.logger = get_logger(__name__)
        self.conversation_history = []
        
        # Initialize Gemini
        api_key = config.get('ai', {}).get('api_key') or os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            self.logger.info("Advanced AI Agent initialized with Gemini API")
        else:
            self.model = None
            self.logger.warning("No Gemini API key provided. AI features will be disabled.")
    
    def process_request(self, user_request, data_manager):
        """Process any user request using pure AI-driven approach"""
        self.logger.info(f"Processing request: '{user_request}'")
        
        if not self.model:
            return "AI features are disabled. Please configure your Gemini API key."
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_request})
        
        try:
            # Get system context
            context = self._gather_system_context(data_manager)
            
            # Generate plan using AI
            plan = self._generate_execution_plan(user_request, context)
            
            if not plan:
                return "I couldn't understand your request. Please try rephrasing."
            
            # Execute the plan step by step
            result = self._execute_plan(plan, data_manager)
            
            # Add result to conversation history
            self.conversation_history.append({"role": "assistant", "content": result})
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return error_msg
    
    def _gather_system_context(self, data_manager):
        """Gather comprehensive system context"""
        context = {
            "available_layers": [],
            "system_info": {},
            "workspace_path": os.getcwd(),
            "installed_packages": self._get_installed_packages(),
            "available_tools": self._get_available_tools()
        }
        
        # Get layer information
        layer_names = data_manager.get_layer_names()
        for layer_name in layer_names:
            info = data_manager.get_layer_info(layer_name)
            if info:
                context["available_layers"].append({
                    "name": layer_name,
                    "geometry_type": info['geometry_type'],
                    "feature_count": info['feature_count'],
                    "columns": info['columns'],
                    "crs": str(info.get('crs', 'Unknown'))
                })
        
        # Get system info
        context["system_info"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        }
        
        return context
    
    def _get_installed_packages(self):
        """Get list of installed Python packages"""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=json"], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception:
            return []
    
    def _get_available_tools(self):
        """Define available tools for the agent"""
        return [
            {
                "name": "execute_python_code",
                "description": "Execute Python code for any analysis or operation",
                "parameters": ["code"]
            }
        ]
    
    def _generate_execution_plan(self, user_request, context):
        """Generate step-by-step execution plan"""
        self.status_update.emit("🧠 Analyzing request and creating execution plan...")
        
        # Get available app functions
        app_functions_info = ""
        if self.app_functions:
            funcs_result = self.app_functions.get_available_functions()
            if funcs_result['success']:
                app_functions_info = json.dumps(funcs_result['functions'], indent=2)
        
        # Create comprehensive prompt
        prompt = f"""You are an advanced autonomous GIS agent. Analyze the user's request and create a detailed execution plan.

USER REQUEST: {user_request}

CURRENTLY LOADED LAYERS (DO NOT READ FROM FILES):
{json.dumps(context['available_layers'], indent=2)}

CRITICAL RULES - NEVER VIOLATE THESE:
1. NEVER use gpd.read_file() or read any files - layers are already loaded!
2. ALWAYS use get_layer(layer_name) to access existing layers
3. Available layer names are: {[layer['name'] for layer in context.get('available_layers', [])]}
4. Use buffer_layer(layer_name, distance, unit) for buffering operations
5. Use add_to_map(gdf, layer_name) to add results to the map
6. Use update_map() to refresh the display

EXECUTION ENVIRONMENT FUNCTIONS:
- get_layer(name): Returns GeoDataFrame of existing layer
- get_layer_names(): Returns list of loaded layer names  
- buffer_layer(layer_name, distance, unit): Creates buffer using app functions
- add_to_map(gdf, name): Adds result to map and updates display
- update_map(): Refreshes map display
- app_functions: Direct access to all app operations

EXAMPLE CORRECT CODE FOR BUFFER:
```python
# Get the existing layer (don't read from file!)
layer_data = get_layer('landuse')
print(f"Got layer with {{len(layer_data)}} features")

# Use the app function to create buffer
result = buffer_layer('landuse', 1000, 'meters')
print(f"Buffer result: {{result}}")

# The buffer_layer function automatically adds to map
```

WRONG - NEVER DO THIS:
```python
# WRONG! Don't read files
landuse = gpd.read_file('landuse.shp')  # DON'T DO THIS!
```

Create a JSON execution plan with ONLY execute_python_code actions:
{{
    "analysis": "What the user wants to accomplish",
    "approach": "Use existing loaded layers and app functions",
    "steps": [
        {{
            "step": 1,
            "action": "execute_python_code",
            "description": "What this code does",
            "parameters": {{
                "code": "Python code using get_layer() and app functions"
            }},
            "expected_outcome": "What should happen"
        }}
    ],
    "success_criteria": "How to know if successful"
}}

AVAILABLE LAYERS: {[layer['name'] for layer in context.get('available_layers', [])]}

Generate ONLY the JSON plan using existing layers:"""

        try:
            response = self.model.generate_content(prompt)
            plan_text = response.text.strip()
            
            # Clean JSON - handle multiple formats
            if plan_text.startswith("```json"):
                plan_text = plan_text[7:]
                if plan_text.endswith("```"):
                    plan_text = plan_text[:-3]
            elif plan_text.startswith("```"):
                plan_text = plan_text[3:]
                if plan_text.endswith("```"):
                    plan_text = plan_text[:-3]
            
            # Remove any leading/trailing whitespace
            plan_text = plan_text.strip()
            
            # Try to parse JSON
            plan = json.loads(plan_text)
            self.logger.info(f"Generated execution plan: {json.dumps(plan, indent=2)}")
            return plan
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            self.logger.error(f"Raw response text: {plan_text}")
            
            # Create a simple fallback plan
            return self._create_fallback_plan(user_request, context)
            
        except Exception as e:
            self.logger.error(f"Error generating plan: {e}")
            return None
    
    def _execute_plan(self, plan, data_manager):
        """Execute the generated plan step by step"""
        self.logger.info("Starting plan execution...")
        self.status_update.emit(f"📋 Executing plan: {plan.get('approach', 'Processing request')}")
        
        results = []
        
        for i, step in enumerate(plan.get('steps', [])):
            step_num = step.get('step', i + 1)
            action = step.get('action')
            description = step.get('description', '')
            parameters = step.get('parameters', {})
            
            self.status_update.emit(f"⚙️ Step {step_num}: {description}")
            self.logger.info(f"Executing step {step_num}: {action} - {description}")
            
            try:
                # Only support execute_python_code - let AI write all logic
                if action == "execute_python_code":
                    result = self._execute_python_code(parameters.get('code', ''), data_manager)
                else:
                    result = f"Unsupported action: {action}. Only execute_python_code is supported."
                
                results.append({"step": step_num, "result": result, "success": True})
                self.logger.info(f"Step {step_num} completed successfully")
                
            except Exception as e:
                error_msg = f"Step {step_num} failed: {str(e)}"
                self.logger.error(error_msg)
                results.append({"step": step_num, "result": error_msg, "success": False})
        
        # Summarize results
        successful_steps = [r for r in results if r['success']]
        failed_steps = [r for r in results if not r['success']]
        
        if failed_steps:
            summary = f"Completed {len(successful_steps)}/{len(results)} steps successfully."
            if failed_steps:
                summary += f"\n\nFailed steps:\n" + "\n".join([f"Step {s['step']}: {s['result']}" for s in failed_steps])
        else:
            summary = f"✅ All {len(results)} steps completed successfully!"
            
            # If we have analysis results, emit them
            final_result = results[-1]['result'] if results else None
            if isinstance(final_result, tuple) and len(final_result) == 2:
                # Assume it's (gdf, layer_name)
                self.analysis_completed.emit(final_result[0], final_result[1])
        
        self.status_update.emit("✅ Plan execution completed")
        return summary
    
    def _execute_python_code(self, code, data_manager):
        """Execute Python code with full access to data and libraries"""
        self.logger.info(f"Executing Python code:\n{code}")
        
        # Create comprehensive execution environment
        execution_env = {
            # Standard libraries
            'os': os,
            'sys': sys,
            'json': json,
            'pandas': pd,
            'geopandas': gpd,
            'numpy': __import__('numpy'),
            'tempfile': tempfile,
            'subprocess': subprocess,
            'Path': Path,
            
            # Data access functions - THESE ARE THE CORRECT WAYS TO ACCESS DATA
            'get_layer': lambda name: data_manager.get_layer(name)['gdf'] if name in data_manager.layers else None,
            'get_layer_names': lambda: data_manager.get_layer_names(),
            'get_layer_info': lambda name: data_manager.get_layer_info(name),
            
            # App functions - centralized operations (preferred methods)
            'app_functions': self.app_functions,
            'buffer_layer': lambda layer_name, distance, unit='meters': self.app_functions.buffer_layer(layer_name, distance, unit) if self.app_functions else None,
            'intersect_layers': lambda l1, l2: self.app_functions.intersect_layers(l1, l2) if self.app_functions else None,
            'select_by_attribute': lambda layer, col, val, op='equals': self.app_functions.select_by_attribute(layer, col, val, op) if self.app_functions else None,
            
            # Map operations
            'add_to_map': lambda gdf, name: self.app_functions.add_analysis_result(gdf, name) if self.app_functions else data_manager.add_analysis_result(gdf, name),
            'update_map': lambda: self.app_functions.update_map() if self.app_functions else None,
            'zoom_to_layer': lambda layer_name: self.app_functions.zoom_to_layer(layer_name) if self.app_functions else None,
            'refresh_ui': lambda: self.app_functions.refresh_ui() if self.app_functions else None,
            
            # File operations (when needed)
            'load_layer': lambda path, name=None: self.app_functions.load_layer(path, name) if self.app_functions else None,
            'export_layer': lambda layer_name, path: self.app_functions.export_layer(layer_name, path) if self.app_functions else None,
            
            # Legacy support (but discourage file reading)
            'add_analysis_result': lambda gdf, name: data_manager.add_analysis_result(gdf, name),
            
            # Results placeholder
            'result_gdf': None,
            'result_layer_name': 'analysis_result',
            'result': None,
            
            # Helper functions
            'print': print,  # Ensure print works
            'len': len,      # Ensure len works
        }
        
        try:
            exec(code, execution_env)
            
            # Return results in priority order
            if execution_env.get('result_gdf') is not None:
                gdf = execution_env['result_gdf']
                layer_name = execution_env.get('result_layer_name', 'analysis_result')
                
                # Use app_functions if available, otherwise fall back to data_manager
                if self.app_functions:
                    add_result = self.app_functions.add_analysis_result(gdf, layer_name)
                    if add_result['success']:
                        final_name = add_result['layer_name']
                        # Update map after adding
                        self.app_functions.update_map()
                    else:
                        final_name = data_manager.add_analysis_result(gdf, layer_name)
                else:
                    final_name = data_manager.add_analysis_result(gdf, layer_name)
                    
                return (gdf, final_name)
            elif execution_env.get('result') is not None:
                return execution_env['result']
            else:
                return "Code executed successfully (no explicit result returned)"
                
        except Exception as e:
            raise Exception(f"Python execution failed: {str(e)}")
    
    def _create_fallback_plan(self, user_request, context):
        """Create a minimal fallback plan if AI output is not valid JSON"""
        self.logger.info("Creating fallback execution plan")
        return {
            "analysis": f"User requested: {user_request}",
            "approach": "Execute Python code using existing layers and app functions",
            "steps": [
                {
                    "step": 1,
                    "action": "execute_python_code",
                    "description": "Process the user request with available data and functions",
                    "parameters": {
                        "code": f"""
# User request: {user_request}
# Available layers: {[layer['name'] for layer in context.get('available_layers', [])]}

print("Processing request:", {repr(user_request)})
print("Available layers:", get_layer_names())

# Example of correct usage:
# layer_data = get_layer('layer_name')  # Get existing layer
# result = buffer_layer('layer_name', 1000, 'meters')  # Use app function

result = 'Please provide more specific instructions for this request.'
"""
                    },
                    "expected_outcome": "Process the request using available functions"
                }
            ],
            "success_criteria": "The code runs without error and uses existing layers"
        }
