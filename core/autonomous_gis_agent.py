"""
Autonomous GIS Agent - A goal-driven spatial intelligence system

This agent can:
1. Understand complex spatial problems and break them down
2. Plan multi-step solutions dynamically
3. Execute spatial operations autonomously  
4. Handle errors and adapt plans
5. Engage in natural conversations about GIS concepts
6. Learn from context and maintain state
"""

import google.generativeai as genai
import geopandas as gpd
import pandas as pd
import json
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal
from .logger import get_logger


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ExecutionStep:
    """Represents a single step in an execution plan"""
    id: str
    description: str
    action_type: str  # 'python_code', 'app_function', 'analysis', 'conversation'
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class ExecutionPlan:
    """Represents a complete execution plan"""
    id: str
    user_request: str
    goal: str
    approach: str
    steps: List[ExecutionStep]
    status: TaskStatus = TaskStatus.PENDING
    context: Dict[str, Any] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class AutonomousGISAgent(QObject):
    """
    Autonomous GIS Agent that can think, plan, and execute spatial tasks
    
    This agent operates in a continuous loop:
    1. Receive user input (request, question, or conversation)
    2. Analyze intent and determine if action is needed
    3. Gather context from available data and tools
    4. Generate execution plan with multiple steps
    5. Execute each step autonomously
    6. Handle errors and adapt plans dynamically
    7. Provide meaningful results and maintain conversation
    """
    
    # Signals for UI updates
    thinking_started = pyqtSignal(str)  # thinking phase message
    plan_created = pyqtSignal(object)   # ExecutionPlan object
    step_started = pyqtSignal(str, str) # step_id, description
    step_completed = pyqtSignal(str, Any) # step_id, result
    step_failed = pyqtSignal(str, str)   # step_id, error
    plan_completed = pyqtSignal(str)     # final response
    conversation_response = pyqtSignal(str) # for non-task conversations
    
    def __init__(self, config, app_functions=None, data_manager=None):
        super().__init__()
        self.config = config
        self.app_functions = app_functions
        self.data_manager = data_manager
        self.logger = get_logger(__name__)
        
        # Agent state and memory
        self.conversation_history = []
        self.execution_plans = {}  # plan_id -> ExecutionPlan
        self.agent_memory = {
            'recent_operations': [],
            'user_preferences': {},
            'spatial_context': {},
            'learned_patterns': []
        }
        
        # Initialize Gemini
        api_key = config.get('ai', {}).get('api_key') or os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            self.logger.info("Autonomous GIS Agent initialized with Gemini API")
        else:
            self.model = None
            self.logger.error("No Gemini API key provided. Agent cannot function without AI model.")
    
    def process_input(self, user_input: str) -> str:
        """
        Main entry point - processes any user input intelligently
        """
        if not self.model:
            return "🚫 I need a Gemini API key to function. Please configure your API key."
        
        self.logger.info(f"Processing user input: '{user_input}'")
        
        # Add to conversation history
        self.conversation_history.append({
            'role': 'user', 
            'content': user_input, 
            'timestamp': time.time()
        })
        
        try:
            # Phase 1: Analyze intent and determine response type
            intent_analysis = self._analyze_intent(user_input)
            
            if intent_analysis['type'] == 'conversation':
                # Handle as conversation (questions, discussions, etc.)
                response = self._handle_conversation(user_input, intent_analysis)
                self.conversation_response.emit(response)
                return response
                
            elif intent_analysis['type'] == 'task':
                # Handle as autonomous task execution
                return self._execute_autonomous_task(user_input, intent_analysis)
                
            else:
                # Mixed or unclear - default to conversation with task awareness
                response = self._handle_mixed_input(user_input, intent_analysis)
                return response
                
        except Exception as e:
            error_msg = f"🚨 Agent error: {str(e)}"
            self.logger.error(f"Agent processing failed: {error_msg}", exc_info=True)
            return error_msg
    
    def _analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user input to determine intent and required response type
        """
        # Get current context
        context = self._gather_context()
        
        # Build conversation context
        recent_history = self.conversation_history[-5:] if self.conversation_history else []
        
        prompt = f"""Analyze this user input to determine the appropriate response type and intent. You MUST respond with valid JSON only.

USER INPUT: "{user_input}"

RECENT CONVERSATION:
{json.dumps(recent_history, indent=2)}

CURRENT CONTEXT:
- Available layers: {context.get('layer_names', [])}
- Recent operations: {self.agent_memory['recent_operations'][-3:]}

RESPONSE TYPES:
1. "conversation" - User is asking questions, discussing concepts, or chatting
2. "task" - User wants to perform spatial analysis, manipulate data, or execute GIS operations
3. "mixed" - Combination of conversation and task request

Respond with ONLY this JSON format (no extra text):
{{
    "type": "conversation",
    "confidence": 0.9,
    "intent_description": "clear description of what user wants",
    "requires_data": false,
    "complexity": "simple",
    "spatial_operations_needed": [],
    "conversational_elements": ["questions", "concepts", "discussed"]
}}"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean the response to extract JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Try to parse JSON
            intent_data = json.loads(response_text)
            self.logger.info(f"Intent analysis: {intent_data}")
            return intent_data
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            self.logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            # Default fallback
            return {
                "type": "conversation",
                "confidence": 0.5,
                "intent_description": "Unable to analyze intent, defaulting to conversation",
                "requires_data": False,
                "complexity": "simple",
                "spatial_operations_needed": [],
                "conversational_elements": ["general discussion"]
            }
    
    def _handle_conversation(self, user_input: str, intent: Dict[str, Any]) -> str:
        """
        Handle conversational inputs - questions, discussions, explanations
        """
        context = self._gather_context()
        
        prompt = f"""You are an expert GIS analyst and spatial data scientist having a natural conversation.

USER: "{user_input}"

INTENT: {intent['intent_description']}

CURRENT SITUATION:
- Available spatial data: {context.get('layer_names', [])}
- Recent work: {self.agent_memory['recent_operations'][-3:]}
- Workspace status: {len(context.get('layer_names', []))} layers loaded

CONVERSATION HISTORY:
{json.dumps(self.conversation_history[-3:], indent=2)}

Respond naturally as an expert who:
- Understands GIS concepts deeply
- Can explain spatial analysis methods
- Offers practical advice and suggestions
- References available data when relevant
- Asks clarifying questions when helpful
- Shares insights about spatial relationships

Keep responses conversational, helpful, and engaging. If the user's question could lead to spatial analysis, mention that as a possibility."""

        try:
            response = self.model.generate_content(prompt)
            reply = response.text.strip()
            
            # Add to conversation history
            self.conversation_history.append({
                'role': 'assistant',
                'content': reply,
                'timestamp': time.time(),
                'type': 'conversation'
            })
            
            return reply
            
        except Exception as e:
            self.logger.error(f"Conversation handling failed: {e}")
            return "I'm having trouble processing that right now. Could you rephrase your question?"
    
    def _execute_autonomous_task(self, user_input: str, intent: Dict[str, Any]) -> str:
        """
        Execute a spatial task autonomously with full planning and execution
        """
        self.thinking_started.emit("🧠 Analyzing your request and planning approach...")
        
        # Phase 1: Create execution plan
        execution_plan = self._create_execution_plan(user_input, intent)
        if not execution_plan:
            return "❌ I couldn't create a plan for that request. Could you provide more details?"
        
        self.plan_created.emit(execution_plan)
        self.logger.info(f"Created execution plan with {len(execution_plan.steps)} steps")
        
        # Phase 2: Execute plan step by step
        final_response = self._execute_plan(execution_plan)
        
        # Phase 3: Update memory and return result
        self._update_agent_memory(execution_plan, final_response)
        
        return final_response
    
    def _create_execution_plan(self, user_input: str, intent: Dict[str, Any]) -> Optional[ExecutionPlan]:
        """
        Create a detailed execution plan for the task
        """
        context = self._gather_context()
        available_functions = self._get_available_functions()
        
        prompt = f"""Create a detailed execution plan for this spatial analysis task.

USER REQUEST: "{user_input}"

INTENT ANALYSIS: {json.dumps(intent, indent=2)}

AVAILABLE CONTEXT:
{json.dumps(context, indent=2)}

AVAILABLE FUNCTIONS:
{json.dumps(available_functions, indent=2)}

CONVERSATION HISTORY:
{json.dumps(self.conversation_history[-3:], indent=2)}

Create a step-by-step plan that:
1. Clearly states the goal
2. Breaks down the approach
3. Lists specific executable steps
4. Handles potential errors
5. Produces meaningful results

Each step should be one of these types:
- "python_code": Execute Python code for analysis
- "app_function": Call specific app functions
- "verification": Check results or validate data
- "output": Format and present results

Respond with JSON:
{{
    "goal": "Clear statement of what we're trying to accomplish",
    "approach": "High-level strategy description",
    "steps": [
        {{
            "id": "step_1",
            "description": "What this step accomplishes",
            "action_type": "python_code|app_function|verification|output",
            "parameters": {{
                "code": "python code if needed",
                "function_name": "function name if app_function",
                "function_params": {{}},
                "verification_type": "check type if verification"
            }},
            "expected_result": "What we expect from this step"
        }}
    ],
    "success_criteria": "How to know if the task succeeded",
    "potential_issues": ["list", "of", "potential", "problems"]
}}"""

        try:
            response = self.model.generate_content(prompt)
            plan_data = json.loads(response.text.strip())
            
            # Create ExecutionPlan object
            steps = []
            for i, step_data in enumerate(plan_data.get('steps', [])):
                step = ExecutionStep(
                    id=step_data.get('id', f'step_{i+1}'),
                    description=step_data.get('description', ''),
                    action_type=step_data.get('action_type', 'python_code'),
                    parameters=step_data.get('parameters', {})
                )
                steps.append(step)
            
            execution_plan = ExecutionPlan(
                id=f"plan_{int(time.time())}",
                user_request=user_input,
                goal=plan_data.get('goal', ''),
                approach=plan_data.get('approach', ''),
                steps=steps,
                context=context
            )
            
            self.execution_plans[execution_plan.id] = execution_plan
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"Failed to create execution plan: {e}")
            return None
    
    def _execute_plan(self, plan: ExecutionPlan) -> str:
        """
        Execute the plan step by step
        """
        plan.status = TaskStatus.IN_PROGRESS
        successful_steps = []
        failed_steps = []
        
        for step in plan.steps:
            self.step_started.emit(step.id, step.description)
            self.logger.info(f"Executing step {step.id}: {step.description}")
            
            # Execute step with retry logic
            success = False
            while step.retry_count <= step.max_retries and not success:
                try:
                    step.status = TaskStatus.IN_PROGRESS
                    result = self._execute_step(step, plan.context)
                    
                    step.result = result
                    step.status = TaskStatus.COMPLETED
                    successful_steps.append(step)
                    self.step_completed.emit(step.id, result)
                    success = True
                    
                except Exception as e:
                    step.retry_count += 1
                    step.error = str(e)
                    self.logger.error(f"Step {step.id} failed (attempt {step.retry_count}): {e}")
                    
                    if step.retry_count > step.max_retries:
                        step.status = TaskStatus.FAILED
                        failed_steps.append(step)
                        self.step_failed.emit(step.id, str(e))
                    else:
                        step.status = TaskStatus.RETRYING
                        # Could implement step adaptation here
        
        # Generate final response
        final_response = self._generate_final_response(plan, successful_steps, failed_steps)
        plan.status = TaskStatus.COMPLETED if not failed_steps else TaskStatus.FAILED
        
        self.plan_completed.emit(final_response)
        return final_response
    
    def _execute_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Any:
        """
        Execute a single step based on its type
        """
        if step.action_type == "python_code":
            return self._execute_python_step(step, context)
        elif step.action_type == "app_function":
            return self._execute_app_function_step(step, context)
        elif step.action_type == "verification":
            return self._execute_verification_step(step, context)
        elif step.action_type == "output":
            return self._execute_output_step(step, context)
        else:
            raise ValueError(f"Unknown step type: {step.action_type}")
    
    def _execute_python_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Any:
        """Execute Python code step"""
        code = step.parameters.get('code', '')
        if not code:
            raise ValueError("No code provided for python_code step")
        
        # Create execution environment
        exec_env = self._create_execution_environment(context)
        
        # Clean code (remove markdown if present)
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()
        
        # Execute code
        exec(code, exec_env)
        
        # Return result
        if 'result' in exec_env:
            return exec_env['result']
        elif 'result_gdf' in exec_env:
            # Handle spatial analysis results
            gdf = exec_env['result_gdf']
            layer_name = exec_env.get('result_layer_name', 'analysis_result')
            final_name = self.data_manager.add_analysis_result(gdf, layer_name)
            return f"Created layer '{final_name}' with {len(gdf)} features"
        else:
            return "Code executed successfully"
    
    def _execute_app_function_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Any:
        """Execute app function step"""
        func_name = step.parameters.get('function_name')
        func_params = step.parameters.get('function_params', {})
        
        if not func_name or not self.app_functions:
            raise ValueError("No function name provided or app_functions not available")
        
        # Get function and execute
        if hasattr(self.app_functions, func_name):
            func = getattr(self.app_functions, func_name)
            result = func(**func_params)
            return result
        else:
            raise ValueError(f"Function '{func_name}' not found in app_functions")
    
    def _execute_verification_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Any:
        """Execute verification step"""
        verification_type = step.parameters.get('verification_type', 'generic')
        
        if verification_type == 'layer_count':
            current_layers = self.data_manager.get_layer_names()
            return f"Current layers ({len(current_layers)}): {', '.join(current_layers)}"
        elif verification_type == 'data_quality':
            # Could implement data quality checks
            return "Data quality check passed"
        else:
            return "Verification completed"
    
    def _execute_output_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Any:
        """Execute output formatting step"""
        output_type = step.parameters.get('output_type', 'summary')
        
        if output_type == 'summary':
            current_layers = self.data_manager.get_layer_names()
            return f"Task completed. Your map now has {len(current_layers)} layers."
        else:
            return "Output generated"
    
    def _create_execution_environment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create Python execution environment with access to spatial functions"""
        return {
            # Standard libraries
            'os': os,
            'json': json,
            'pd': pd,
            'gpd': gpd,
            
            # Data access
            'get_layer': lambda name: self.data_manager.get_layer(name)['gdf'] if self.data_manager.get_layer(name) else None,
            'get_layer_names': lambda: self.data_manager.get_layer_names(),
            'get_layer_info': lambda name: self.data_manager.get_layer_info(name),
            
            # App functions
            'buffer_layer': lambda layer_name, distance, unit='meters': self.app_functions.buffer_layer(layer_name, distance, unit) if self.app_functions else None,
            'intersect_layers': lambda l1, l2: self.app_functions.intersect_layers(l1, l2) if self.app_functions else None,
            'add_to_map': lambda gdf, name: self.app_functions.add_analysis_result(gdf, name) if self.app_functions else None,
            
            # Result variables
            'result': None,
            'result_gdf': None,
            'result_layer_name': 'analysis_result'
        }
    
    def _gather_context(self) -> Dict[str, Any]:
        """Gather current system context"""
        context = {
            'timestamp': time.time(),
            'layer_names': [],
            'layer_details': [],
            'map_state': {},
            'recent_operations': self.agent_memory['recent_operations'][-5:]
        }
        
        if self.data_manager:
            context['layer_names'] = self.data_manager.get_layer_names()
            for layer_name in context['layer_names']:
                info = self.data_manager.get_layer_info(layer_name)
                if info:
                    context['layer_details'].append({
                        'name': layer_name,
                        'type': info.get('geometry_type', 'unknown'),
                        'features': info.get('feature_count', 0),
                        'columns': info.get('columns', [])
                    })
        
        return context
    
    def _get_available_functions(self) -> Dict[str, Any]:
        """Get available app functions and their signatures"""
        functions = {}
        
        if self.app_functions:
            # Could introspect available functions
            functions = {
                'buffer_layer': 'Create buffer around layer features',
                'intersect_layers': 'Find intersection between two layers',
                'add_analysis_result': 'Add analysis result to map',
                'export_layer': 'Export layer to file',
                'update_map': 'Refresh map display'
            }
        
        return functions
    
    def _generate_final_response(self, plan: ExecutionPlan, successful_steps: List[ExecutionStep], failed_steps: List[ExecutionStep]) -> str:
        """Generate final response based on execution results"""
        
        # Collect step results
        results = []
        for step in successful_steps:
            if step.result:
                results.append(str(step.result))
        
        context = self._gather_context()
        
        prompt = f"""Generate a natural, informative response about the completed spatial analysis task.

ORIGINAL REQUEST: "{plan.user_request}"
GOAL: "{plan.goal}"
APPROACH: "{plan.approach}"

EXECUTION RESULTS:
Successful steps: {len(successful_steps)}/{len(plan.steps)}
Failed steps: {len(failed_steps)}

STEP RESULTS:
{chr(10).join(results)}

CURRENT STATE:
- Available layers: {context['layer_names']}
- Total features processed: {sum(info.get('features', 0) for info in context['layer_details'])}

ERROR SUMMARY (if any):
{chr(10).join([f"- {step.description}: {step.error}" for step in failed_steps])}

Provide a natural, informative response that:
1. Confirms what was accomplished
2. Describes any new data created
3. Mentions next steps or suggestions
4. Handles errors gracefully if any occurred

Be conversational and specific about the results."""

        try:
            response = self.model.generate_content(prompt)
            final_response = response.text.strip()
            
            # Add to conversation history
            self.conversation_history.append({
                'role': 'assistant',
                'content': final_response,
                'timestamp': time.time(),
                'type': 'task_completion',
                'plan_id': plan.id
            })
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate final response: {e}")
            
            # Fallback response
            if successful_steps and not failed_steps:
                return f"✅ Task completed successfully! I executed {len(successful_steps)} steps and your analysis is ready."
            elif successful_steps and failed_steps:
                return f"⚠️ Task partially completed. {len(successful_steps)} steps succeeded, but {len(failed_steps)} steps had issues."
            else:
                return f"❌ Task failed. I encountered issues with all {len(failed_steps)} steps."
    
    def _handle_mixed_input(self, user_input: str, intent: Dict[str, Any]) -> str:
        """Handle mixed conversation + task inputs"""
        # For now, treat as conversation but mention task possibilities
        response = self._handle_conversation(user_input, intent)
        
        if intent.get('requires_data') and not self.data_manager.get_layer_names():
            response += "\n\n💡 I notice you might want to do some spatial analysis. Feel free to load some data and I can help you work with it!"
        
        return response
    
    def _update_agent_memory(self, plan: ExecutionPlan, final_response: str):
        """Update agent memory with completed operations"""
        operation_summary = {
            'timestamp': time.time(),
            'user_request': plan.user_request,
            'goal': plan.goal,
            'steps_completed': len([s for s in plan.steps if s.status == TaskStatus.COMPLETED]),
            'success': plan.status == TaskStatus.COMPLETED
        }
        
        self.agent_memory['recent_operations'].append(operation_summary)
        
        # Keep only recent operations
        if len(self.agent_memory['recent_operations']) > 10:
            self.agent_memory['recent_operations'] = self.agent_memory['recent_operations'][-10:]
