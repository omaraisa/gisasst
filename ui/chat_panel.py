from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QTextCursor
import time

class ChatWorker(QThread):
    """Worker thread for AI chat processing"""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ai_agent, user_input):
        super().__init__()
        self.ai_agent = ai_agent
        self.user_input = user_input
        
    def run(self):
        try:
            # Process input using autonomous agent
            response = self.ai_agent.process_input(self.user_input)
            self.response_ready.emit(response)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class ChatPanel(QWidget):
    """Chat panel for AI interaction"""
    
    map_update_requested = pyqtSignal()
    
    def __init__(self, ai_agent, data_manager, map_manager):
        super().__init__()
        self.ai_agent = ai_agent
        self.data_manager = data_manager
        self.map_manager = map_manager
        self.chat_worker = None
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("🤖 AI Assistant")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Chat history
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMaximumHeight(300)
        
        # Set font
        font = QFont("Consolas", 9)
        self.chat_display.setFont(font)
        
        # Welcome message
        self.add_message("AI", "Hello! I'm your GIS assistant. You can ask me to perform spatial analysis on your loaded layers.\n\nExamples:\n• Create a 500 meter buffer around roads\n• Select buildings with type = 'residential'\n• Find intersection of parcels and flood zones", "system")
        
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QVBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask a spatial analysis question...")
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        
        button_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_chat)
        button_layout.addWidget(self.clear_button)
        
        input_layout.addLayout(button_layout)
        layout.addLayout(input_layout)
        
        # Example questions
        examples_label = QLabel("💡 Example Questions:")
        examples_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 10px;")
        layout.addWidget(examples_label)
        
        examples_scroll = QScrollArea()
        examples_scroll.setMaximumHeight(100)
        examples_scroll.setWidgetResizable(True)
        examples_widget = QWidget()
        examples_layout = QVBoxLayout(examples_widget)
        
        example_questions = [
            "Buffer the roads layer by 100 meters",
            "Select all points within 500m of roads",
            "Find intersection between parcels and flood zones",
            "Dissolve polygons by 'category' attribute",
            "Create 1km buffer around hospitals"
        ]
        
        for question in example_questions:
            btn = QPushButton(f"📝 {question}")
            btn.setStyleSheet("text-align: left; padding: 3px; border: 1px solid #ccc;")
            btn.clicked.connect(lambda checked, q=question: self.set_question(q))
            examples_layout.addWidget(btn)
        
        examples_scroll.setWidget(examples_widget)
        layout.addWidget(examples_scroll)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Connect autonomous agent signals
        if hasattr(self.ai_agent, 'thinking_started'):
            self.ai_agent.thinking_started.connect(self.on_thinking_started)
        if hasattr(self.ai_agent, 'plan_created'):
            self.ai_agent.plan_created.connect(self.on_plan_created)
        if hasattr(self.ai_agent, 'step_started'):
            self.ai_agent.step_started.connect(self.on_step_started)
        if hasattr(self.ai_agent, 'step_completed'):
            self.ai_agent.step_completed.connect(self.on_step_completed)
        if hasattr(self.ai_agent, 'step_failed'):
            self.ai_agent.step_failed.connect(self.on_step_failed)
        if hasattr(self.ai_agent, 'plan_completed'):
            self.ai_agent.plan_completed.connect(self.on_plan_completed)
        if hasattr(self.ai_agent, 'conversation_response'):
            self.ai_agent.conversation_response.connect(self.on_conversation_response)
        
        # Legacy connections for backward compatibility
        if hasattr(self.ai_agent, 'analysis_completed'):
            self.ai_agent.analysis_completed.connect(self.on_analysis_completed)
        if hasattr(self.ai_agent, 'analysis_failed'):
            self.ai_agent.analysis_failed.connect(self.on_analysis_failed)
        if hasattr(self.ai_agent, 'status_update'):
            self.ai_agent.status_update.connect(self.on_status_update)
        
    def add_message(self, sender, message, msg_type="user"):
        """Add a message to the chat display"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        timestamp = time.strftime("%H:%M:%S")
        
        if msg_type == "system":
            self.chat_display.setTextColor(self.chat_display.palette().color(self.chat_display.palette().WindowText))
            cursor.insertText(f"[{timestamp}] {message}\n\n")
        elif sender == "You":
            self.chat_display.setTextColor(self.chat_display.palette().color(self.chat_display.palette().Link))
            cursor.insertText(f"[{timestamp}] You: {message}\n")
        else:
            self.chat_display.setTextColor(self.chat_display.palette().color(self.chat_display.palette().WindowText))
            cursor.insertText(f"[{timestamp}] AI: {message}\n\n")
        
        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def set_question(self, question):
        """Set a predefined question"""
        self.chat_input.setText(question)
        
    def send_message(self):
        """Send message to AI"""
        user_input = self.chat_input.text().strip()
        if not user_input:
            return
            
        # Add user message
        self.add_message("You", user_input)
        self.chat_input.clear()
        
        # Disable input while processing
        self.set_input_enabled(False)
        
        # Start worker thread
        self.chat_worker = ChatWorker(self.ai_agent, user_input)
        self.chat_worker.response_ready.connect(self.on_response_ready)
        self.chat_worker.error_occurred.connect(self.on_error_occurred)
        self.chat_worker.start()
        
    @pyqtSlot(str)
    def on_response_ready(self, response):
        """Handle AI response - only for non-autonomous responses"""
        # For autonomous agent, signals are handled separately
        # This is mainly for fallback or direct responses
        if response:
            self.add_message("AI", response)
        
        # Re-enable input
        self.set_input_enabled(True)
        
    @pyqtSlot(str)
    def on_error_occurred(self, error):
        """Handle error"""
        self.add_message("AI", f"❌ Error: {error}")
        
        # Re-enable input
        self.set_input_enabled(True)
        
    def on_analysis_completed(self, result_gdf, layer_name):
        """Handle successful analysis completion"""
        self.map_update_requested.emit()
        
    def on_analysis_failed(self, error_message):
        """Handle analysis failure"""
        self.add_message("AI", f"❌ Analysis failed: {error_message}")
        
    def on_status_update(self, status_message):
        """Handle status updates from advanced agent"""
        self.add_message("AI", f"🔄 {status_message}", "system")
    
    def remove_last_message(self):
        """Remove the last message (used to remove processing indicator)"""
        text = self.chat_display.toPlainText()
        lines = text.split('\n')
        
        # Find and remove the last AI message
        for i in range(len(lines) - 1, -1, -1):
            if "🔄 Processing" in lines[i]:
                lines.pop(i)
                break
                
        self.chat_display.setPlainText('\n'.join(lines))
        
        # Move cursor to end
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
        
    def set_input_enabled(self, enabled):
        """Enable/disable input controls"""
        self.chat_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        
        if enabled:
            self.send_button.setText("Send")
            self.chat_input.setFocus()
        else:
            self.send_button.setText("⏳")
            
    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.clear()
        self.add_message("AI", "Chat cleared. How can I help you with spatial analysis?", "system")
        
    @pyqtSlot(str)
    def on_thinking_started(self, message):
        """Handle thinking started signal"""
        self.add_message("AI", f"🧠 {message}", "system")
    
    @pyqtSlot(str, str)
    def on_step_started(self, step_id, description):
        """Handle step started signal"""
        self.add_message("AI", f"🔄 {description}", "system")
    
    @pyqtSlot(str, object)
    def on_step_completed(self, step_id, result):
        """Handle step completed signal"""
        if result and len(str(result)) > 100:
            # Truncate long results
            result_str = str(result)[:100] + "..."
        else:
            result_str = str(result)
        self.add_message("AI", f"✅ Step completed: {result_str}", "system")
    
    @pyqtSlot(object)
    def on_plan_created(self, plan):
        """Handle plan created signal"""
        self.add_message("AI", f"📋 Created execution plan: {plan.goal}", "system")
        self.add_message("AI", f"📝 Approach: {plan.approach}", "system")
        self.add_message("AI", f"🔢 Steps to execute: {len(plan.steps)}", "system")
    
    @pyqtSlot(str, str)
    def on_step_failed(self, step_id, error):
        """Handle step failed signal"""
        self.add_message("AI", f"❌ {step_id}: {error}", "system")
    
    @pyqtSlot(str)
    def on_plan_completed(self, final_response):
        """Handle plan completion - this is the main response"""
        self.add_message("AI", final_response)
        self.map_update_requested.emit()
        # Re-enable input after task completion
        self.set_input_enabled(True)
    
    @pyqtSlot(str)
    def on_conversation_response(self, response):
        """Handle conversational response"""
        self.add_message("AI", response)
        # Re-enable input after conversation
        self.set_input_enabled(True)
