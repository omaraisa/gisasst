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
        
        # Handle simple conversational requests without formal planning
        user_lower = user_request.lower().strip()
        
        # Simple greetings and social interactions
        if user_lower in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']:
            return self._create_simple_response(f"Hi there! I'm your GIS assistant. I can help you analyze spatial data, manage layers, and perform various GIS operations. You currently have {len(context.get('available_layers', []))} layer(s) loaded. What would you like to do?")
        
        # Simple queries that don't need complex planning
        if user_lower in ['help', 'what can you do', 'what can you do?']:
            return self._create_simple_response("I can help you with various GIS tasks like:\n• Analyzing spatial data\n• Creating buffers around features\n• Finding intersections between layers\n• Measuring distances and areas\n• Managing map layers\n• Exporting results\n\nJust ask me in plain English what you'd like to do!")
        
        if 'how many layers' in user_lower or 'list layers' in user_lower:
            layers = [layer['name'] for layer in context.get('available_layers', [])]
            if layers:
                return self._create_simple_response(f"You have {len(layers)} layer(s) loaded: {', '.join(layers)}")
            else:
                return self._create_simple_response("No layers are currently loaded. Would you like me to help you load some data?")
        
        # For complex requests, use full AI planning
        self.status_update.emit("🧠 Analyzing request and creating execution plan...")
        
        # Get available app functions
        app_functions_info = ""
        if self.app_functions:
            funcs_result = self.app_functions.get_available_functions()
            if funcs_result['success']:
                app_functions_info = json.dumps(funcs_result['functions'], indent=2)
        
        # Create comprehensive prompt
        prompt = f"""You are a friendly, helpful GIS assistant. Analyze the user's request and respond naturally while being precise about technical operations.

USER REQUEST: {user_request}

CURRENTLY LOADED LAYERS:
{json.dumps(context['available_layers'], indent=2)}

IMPORTANT GUIDELINES:
1. Be conversational and friendly - speak like a helpful colleague, not a robot
2. NEVER use gpd.read_file() - all layers are already loaded and available
3. Always use get_layer(layer_name) to access existing layers
4. Available layer names: {[layer['name'] for layer in context.get('available_layers', [])]}
5. Use app functions like buffer_layer(), add_to_map() for operations
6. Set 'result' variable with natural, helpful responses

AVAILABLE FUNCTIONS:
- get_layer(name): Get existing layer data
- get_layer_names(): List all loaded layers
- buffer_layer(layer_name, distance, unit): Create buffer zones
- add_to_map(gdf, name): Display results on map
- app_functions: Access to all GIS operations

RESPONSE STYLE EXAMPLES:
- Simple queries: "You have 3 layers loaded: roads, buildings, and parks"
- Operations: "Great! I've created a 500-meter buffer around your roads layer"
- Errors: "I couldn't find that layer. You currently have: roads, buildings, parks"

EXAMPLE CODE:
```python
# Natural response for layer count
layer_names = get_layer_names()
if layer_names:
    result = f"You have {{len(layer_names)}} layer{{'' if len(layer_names) == 1 else 's'}} loaded: {{', '.join(layer_names)}}"
else:
    result = "No layers are currently loaded. Would you like me to help you load some data?"

# Friendly buffer operation
buffer_result = buffer_layer('roads', 500, 'meters')
if buffer_result['success']:
    add_to_map(buffer_result['layer'], buffer_result['result_layer'])
    result = f"Perfect! I've created a 500-meter buffer around your roads layer. The new '{buffer_result['result_layer']}' layer has {buffer_result['feature_count']} features and is now visible on your map."
else:
    result = f"I ran into an issue creating the buffer: {buffer_result['message']}"
```

Create a JSON plan that produces natural, conversational responses:
{{
    "analysis": "What the user wants to accomplish",
    "approach": "Use existing loaded layers and provide clear feedback",
    "steps": [
        {{
            "step": 1,
            "action": "execute_python_code",
            "description": "What this code does",
            "parameters": {{
                "code": "Python code that sets 'result' variable with user feedback"
            }},
            "expected_outcome": "What should happen"
        }}
    ],
    "success_criteria": "How to know if successful"
}}

AVAILABLE LAYERS: {[layer['name'] for layer in context.get('available_layers', [])]}

Generate ONLY the JSON plan with proper result reporting:"""

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
        
        # Summarize results with proper user feedback
        successful_steps = [r for r in results if r['success']]
        failed_steps = [r for r in results if not r['success']]
        
        if failed_steps:
            summary = f"I encountered some issues while processing your request."
            if successful_steps:
                summary += f" I completed {len(successful_steps)} out of {len(results)} steps."
            summary += "\n\nHere's what went wrong:\n" + "\n".join([f"• {s['result']}" for s in failed_steps])
        else:
            # Check if this was a simple conversational response
            is_simple_response = (len(results) == 1 and 
                                results[0].get('result', '').startswith('result = """') and 
                                results[0].get('result', '').endswith('"""'))
            
            if is_simple_response:
                # Extract and return the conversational message
                result_text = results[0]['result']
                start = result_text.find('"""') + 3
                end = result_text.rfind('"""')
                if start > 2 and end > start:
                    return result_text[start:end].strip()
            
            # For analysis operations, provide contextual feedback
            summary = ""
            
            # Extract meaningful results
            for result in results:
                result_content = result.get('result', '')
                
                # Handle different types of results
                if isinstance(result_content, str):
                    # Check if it's Python execution feedback
                    if result_content.startswith("Code executed successfully"):
                        continue  # Skip generic execution messages
                    
                    # If it contains meaningful information, use it as the primary response
                    if (result_content and 
                        not result_content.startswith("No output") and
                        len(result_content) > 10):  # Meaningful content
                        # This is likely the actual result from the 'result' variable
                        return result_content  # Return immediately, don't concatenate
                        
                elif isinstance(result_content, (int, float)):
                    summary += f"{result_content}"
                elif isinstance(result_content, (list, tuple)) and result_content:
                    if len(result_content) <= 5:
                        summary += f"{', '.join(str(x) for x in result_content)}"
                    else:
                        summary += f"{len(result_content)} items"
            
            # If no meaningful summary was found, provide a friendly default
            if not summary.strip():
                summary = "Done! Your request has been processed successfully."
            
            # Add context about current layers only for analysis operations
            try:
                current_layers = data_manager.get_layer_names()
                if current_layers and "buffer" in str(results).lower():
                    # Only show layer context for operations that likely changed the map
                    summary += f"\n\nYour map now has {len(current_layers)} layer(s): {', '.join(current_layers)}"
            except Exception:
                pass
        
        self.status_update.emit("✅ Plan execution completed")
        return summary
    
    def _execute_python_code(self, code, data_manager):
        """Execute Python code with full access to data and libraries"""
        
        # Clean the code - remove markdown formatting if present
        if isinstance(code, str):
            code = code.strip()
            # Remove markdown code blocks
            if code.startswith("```python"):
                code = code[9:]  # Remove ```python
            elif code.startswith("```"):
                code = code[3:]   # Remove ```
            
            if code.endswith("```"):
                code = code[:-3]  # Remove trailing ```
            
            code = code.strip()
        
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
            
            # Map operations - handle both GeoDataFrame and layer objects
            'add_to_map': lambda layer_or_gdf, name=None: self._add_to_map_helper(layer_or_gdf, name, data_manager),
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
            
            # Return results in priority order with better feedback
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
                        return (gdf, final_name)
                    else:
                        final_name = data_manager.add_analysis_result(gdf, layer_name)
                        return (gdf, final_name)
                else:
                    final_name = data_manager.add_analysis_result(gdf, layer_name)
                    return (gdf, final_name)
                    
            elif execution_env.get('result') is not None:
                result_value = execution_env['result']
                # If the result contains the friendly message from the buffer operation
                if isinstance(result_value, str) and len(result_value) > 20:  # Likely a meaningful message
                    return result_value
                return result_value
            else:
                # Check if any output was captured during execution
                # Look for common result patterns in the executed code
                if 'get_layer_names()' in code and 'print(' in code:
                    layer_names = data_manager.get_layer_names()
                    return f"Current layers ({len(layer_names)}): {', '.join(layer_names)}"
                elif 'len(' in code and 'get_layer_names' in code:
                    layer_count = len(data_manager.get_layer_names())
                    return f"Number of layers on map: {layer_count}"
                elif 'buffer_layer(' in code:
                    return "Buffer operation completed successfully"
                else:
                    return "Code executed successfully"
                
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
    
    def _create_simple_response(self, message):
        """Create a simple response for conversational queries"""
        return {
            'plan': [{
                'step': 1,
                'description': 'Provide conversational response',
                'action': 'respond',
                'code': f'result = """{message}"""'
            }],
            'reasoning': 'Simple conversational response',
            'confidence': 1.0,
            'requires_execution': True
        }
    
    def _add_to_map_helper(self, layer_or_gdf, name, data_manager):
        """Helper to handle adding different types of layers to map"""
        try:
            # If it's already a GeoDataFrame, add it directly
            if hasattr(layer_or_gdf, 'geometry'):
                if self.app_functions:
                    result = self.app_functions.add_analysis_result(layer_or_gdf, name)
                    self.app_functions.update_map()
                    return result
                else:
                    return data_manager.add_analysis_result(layer_or_gdf, name)
            
            # If it's a layer dict with 'layer' key (from buffer_layer result)
            elif isinstance(layer_or_gdf, dict) and 'layer' in layer_or_gdf:
                gdf = layer_or_gdf['layer']
                if self.app_functions:
                    result = self.app_functions.add_analysis_result(gdf, name)
                    self.app_functions.update_map()
                    return result
                else:
                    return data_manager.add_analysis_result(gdf, name)
                    
            else:
                return f"Could not add layer to map - unexpected data type: {type(layer_or_gdf)}"
                
        except Exception as e:
            return f"Error adding layer to map: {str(e)}"
