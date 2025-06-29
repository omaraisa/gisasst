#!/usr/bin/env python3
"""
Rollback script to revert to the original AI agent if needed

Use this if you encounter issues with the advanced agent.
"""

import shutil
from pathlib import Path

def rollback_to_original_agent():
    """Rollback to the original AI agent"""
    print("🔄 Rolling back to original AI agent...")
    
    try:
        # Create backup copies of modified files
        files_to_restore = [
            'main.py',
            'ui/chat_panel.py'
        ]
        
        # Read current main.py and replace advanced agent with original
        main_py = Path('main.py')
        if main_py.exists():
            content = main_py.read_text()
            
            # Replace imports
            content = content.replace(
                'from core.advanced_ai_agent import AdvancedGISAgent',
                ''
            )
            
            # Replace initialization
            content = content.replace(
                'self.ai_agent = AdvancedGISAgent(self.config)  # Using Advanced Agent',
                'self.ai_agent = AIAgent(self.config)'
            )
            
            main_py.write_text(content)
            print("✅ Restored main.py")
        
        # Read current chat_panel.py and restore original method call
        chat_panel = Path('ui/chat_panel.py')
        if chat_panel.exists():
            content = chat_panel.read_text()
            
            # Replace the run method with original version
            original_run_method = '''    def run(self):
        try:
            response = self.ai_agent.process_question(self.question, self.data_manager)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))'''
            
            # Find and replace the advanced version
            lines = content.split('\n')
            new_lines = []
            in_run_method = False
            indent_count = 0
            
            for line in lines:
                if 'def run(self):' in line:
                    in_run_method = True
                    indent_count = len(line) - len(line.lstrip())
                    new_lines.extend(original_run_method.split('\n'))
                    continue
                elif in_run_method:
                    current_indent = len(line) - len(line.lstrip())
                    if line.strip() and current_indent <= indent_count and not line.startswith(' ' * (indent_count + 1)):
                        in_run_method = False
                        new_lines.append(line)
                    elif not in_run_method:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # Remove advanced agent connections
            content = '\n'.join(new_lines)
            content = content.replace('''        # Connect status updates for advanced agent
        if hasattr(self.ai_agent, 'status_update'):
            self.ai_agent.status_update.connect(self.on_status_update)''', '')
            
            # Remove status update handler
            content = content.replace('''    def on_status_update(self, status_message):
        """Handle status updates from advanced agent"""
        self.add_message("AI", f"🔄 {status_message}", "system")
    
    # ...existing code...''', '')
            
            chat_panel.write_text(content)
            print("✅ Restored ui/chat_panel.py")
        
        print("\n🎉 Rollback completed successfully!")
        print("\nYour application is now using the original AI agent.")
        print("You can start the application normally with: python main.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        print("\nManual rollback required:")
        print("1. In main.py:")
        print("   - Remove: from core.advanced_ai_agent import AdvancedGISAgent")
        print("   - Change: self.ai_agent = AdvancedGISAgent(self.config)")
        print("   - To:     self.ai_agent = AIAgent(self.config)")
        print("\n2. In ui/chat_panel.py:")
        print("   - Restore original process_question call in run() method")
        print("   - Remove status_update connections")
        return False

if __name__ == "__main__":
    print("🔄 AI Agent Rollback Tool")
    print("=" * 30)
    
    confirm = input("Are you sure you want to rollback to the original agent? (y/N): ")
    if confirm.lower() == 'y':
        rollback_to_original_agent()
    else:
        print("Rollback cancelled.")
