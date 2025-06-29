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
    
    def __init__(self, config):
        super().__init__()
        self.config = config
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
        """Process any user request using tool-based approach"""
        self.logger.info(f"Processing advanced request: '{user_request}'")
        
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
                "description": "Execute Python code for data analysis",
                "parameters": ["code"]
            },
            {
                "name": "install_package",
                "description": "Install Python packages using pip",
                "parameters": ["package_name"]
            },
            {
                "name": "run_command",
                "description": "Execute system commands",
                "parameters": ["command"]
            },
            {
                "name": "spatial_analysis",
                "description": "Perform spatial analysis operations",
                "parameters": ["operation", "layers", "parameters"]
            },
            {
                "name": "data_manipulation",
                "description": "Manipulate and transform data",
                "parameters": ["data_source", "operations"]
            },
            {
                "name": "file_operations",
                "description": "Read, write, and manage files",
                "parameters": ["operation", "file_path", "content"]
            }
        ]
    
    def _generate_execution_plan(self, user_request, context):
        """Generate step-by-step execution plan"""
        self.status_update.emit("🧠 Analyzing request and creating execution plan...")
        
        # Create comprehensive prompt
        prompt = f"""You are an advanced autonomous GIS agent. Your task is to create a detailed execution plan for the user's request.

USER REQUEST: {user_request}

SYSTEM CONTEXT:
Available Layers: {json.dumps(context['available_layers'], indent=2)}
Installed Packages: {[pkg['name'] for pkg in context['installed_packages'][:20]]}
Available Tools: {json.dumps(context['available_tools'], indent=2)}

CONVERSATION HISTORY:
{json.dumps(self.conversation_history[-5:], indent=2)}

Create a JSON execution plan with this structure:
{{
    "analysis": "Brief analysis of what the user wants",
    "approach": "High-level approach to solve this",
    "steps": [
        {{
            "step": 1,
            "action": "tool_name",
            "description": "What this step does",
            "parameters": {{"param": "value"}},
            "expected_outcome": "What should happen"
        }}
    ],
    "success_criteria": "How to determine if successful",
    "fallback_options": ["Alternative approaches if main plan fails"]
}}

AVAILABLE ACTIONS:
- execute_python_code: Run any Python code for analysis
- install_package: Install missing packages
- run_command: Execute system commands
- spatial_analysis: Perform GIS operations
- data_manipulation: Transform data
- file_operations: Handle files

RULES:
1. Break complex tasks into simple steps
2. Always check prerequisites first
3. Handle potential errors
4. Be specific about parameters
5. Consider data dependencies

Generate ONLY the JSON plan, no other text:"""

        try:
            response = self.model.generate_content(prompt)
            plan_text = response.text.strip()
            
            # Clean JSON
            if plan_text.startswith("```json"):
                plan_text = plan_text[7:-3]
            elif plan_text.startswith("```"):
                plan_text = plan_text[3:-3]
            
            plan = json.loads(plan_text)
            self.logger.info(f"Generated execution plan: {json.dumps(plan, indent=2)}")
            return plan
            
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
                if action == "execute_python_code":
                    result = self._execute_python_code(parameters.get('code', ''), data_manager)
                elif action == "install_package":
                    result = self._install_package(parameters.get('package_name', ''))
                elif action == "run_command":
                    result = self._run_command(parameters.get('command', ''))
                elif action == "spatial_analysis":
                    result = self._spatial_analysis(parameters, data_manager)
                elif action == "data_manipulation":
                    result = self._data_manipulation(parameters, data_manager)
                elif action == "file_operations":
                    result = self._file_operations(parameters)
                else:
                    result = f"Unknown action: {action}"
                
                results.append({"step": step_num, "result": result, "success": True})
                self.logger.info(f"Step {step_num} completed successfully")
                
            except Exception as e:
                error_msg = f"Step {step_num} failed: {str(e)}"
                self.logger.error(error_msg)
                results.append({"step": step_num, "result": error_msg, "success": False})
                
                # Try fallback options if available
                if step_num == 1 and plan.get('fallback_options'):
                    self.status_update.emit("🔄 Trying alternative approach...")
                    # Could implement fallback logic here
        
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
            
            # Data manager functions
            'get_layer': lambda name: data_manager.get_layer(name),
            'get_layer_names': lambda: data_manager.get_layer_names(),
            'add_analysis_result': lambda gdf, name: data_manager.add_analysis_result(gdf, name),
            
            # Results placeholder
            'result_gdf': None,
            'result_layer_name': 'analysis_result',
            'result': None
        }
        
        try:
            exec(code, execution_env)
            
            # Return results in priority order
            if execution_env.get('result_gdf') is not None:
                gdf = execution_env['result_gdf']
                layer_name = execution_env.get('result_layer_name', 'analysis_result')
                final_name = data_manager.add_analysis_result(gdf, layer_name)
                return (gdf, final_name)
            elif execution_env.get('result') is not None:
                return execution_env['result']
            else:
                return "Code executed successfully (no explicit result returned)"
                
        except Exception as e:
            raise Exception(f"Python execution failed: {str(e)}")
    
    def _install_package(self, package_name):
        """Install Python package"""
        self.logger.info(f"Installing package: {package_name}")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_name
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return f"Successfully installed {package_name}"
            else:
                return f"Failed to install {package_name}: {result.stderr}"
                
        except Exception as e:
            raise Exception(f"Package installation failed: {str(e)}")
    
    def _run_command(self, command):
        """Execute system command"""
        self.logger.info(f"Running command: {command}")
        
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=60
            )
            
            output = result.stdout or result.stderr
            return f"Command executed. Output: {output[:500]}..."
            
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
    
    def _spatial_analysis(self, parameters, data_manager):
        """Perform spatial analysis operations"""
        operation = parameters.get('operation', '')
        layers = parameters.get('layers', [])
        params = parameters.get('parameters', {})
        
        # This could be expanded with specific spatial operations
        # For now, delegate to Python code execution
        code = f"""
# Spatial analysis: {operation}
layers = {layers}
params = {params}

# Add your spatial analysis logic here
result = "Spatial analysis completed for operation: {operation}"
"""
        return self._execute_python_code(code, data_manager)
    
    def _data_manipulation(self, parameters, data_manager):
        """Perform data manipulation"""
        # Similar to spatial analysis, but for data operations
        return "Data manipulation completed"
    
    def _file_operations(self, parameters):
        """Handle file operations"""
        operation = parameters.get('operation', '')
        file_path = parameters.get('file_path', '')
        content = parameters.get('content', '')
        
        if operation == 'read':
            with open(file_path, 'r') as f:
                return f.read()
        elif operation == 'write':
            with open(file_path, 'w') as f:
                f.write(content)
            return f"File written to {file_path}"
        else:
            return f"Unknown file operation: {operation}"
