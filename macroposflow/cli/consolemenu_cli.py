"""
Console-menu based CLI implementation for MacroPosFlow.

This module provides a comprehensive console-based menu interface using the console-menu library
with full Phase 2 functionality including state management, configurable key bindings, loop support,
and advanced recording/execution features.
"""

import logging
import threading
import time
from typing import List, Dict, Any, Optional

# Import console-menu library correctly
from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem, SubmenuItem
from consolemenu.format import AsciiBorderStyle

from ..settings import SettingsManager
from ..state_manager import StateManager, ProcessState
from ..recorder import ActionRecorder
from ..executor import ActionExecutor
from ..config import ConfigManager

logger = logging.getLogger(__name__)


class ConsoleMenuCLI:
    """
    CLI implementation using console-menu library with advanced features.
    
    This class provides a comprehensive menu-driven interface for MacroPosFlow functionality
    including state management, configurable key bindings, loop support, and settings management.
    """
    
    def __init__(self):
        """Initialize the CLI interface."""
        # Initialize managers
        self.settings_manager = SettingsManager()
        self.state_manager = StateManager()
        self.config_manager = ConfigManager()
        
        # Initialize recorder and executor with new managers
        self.recorder = ActionRecorder(
            settings_manager=self.settings_manager,
            state_manager=self.state_manager,
            on_action_recorded=self._on_action_recorded
        )
        self.executor = ActionExecutor(
            settings_manager=self.settings_manager,
            state_manager=self.state_manager,
            dry_run=False
        )
        
        # Set up executor callbacks
        self.executor.set_callbacks(
            on_action_start=self._on_action_start,
            on_action_complete=self._on_action_complete,
            on_execution_start=self._on_execution_start,
            on_execution_complete=self._on_execution_complete,
            on_execution_error=self._on_execution_error,
            on_loop_start=self._on_loop_start,
            on_loop_complete=self._on_loop_complete
        )
        
        # Current state
        self.current_actions: List[Dict[str, Any]] = []
        self.current_macro_name: str = ""
        
        # UI state
        self.last_update_time = 0.0
        self.status_update_interval = 0.5  # Update status every 0.5 seconds
        
        # Initialize menu
        self._setup_menu()
        
        # Set up state change callbacks
        self.state_manager.add_recording_state_callback(self._on_recording_state_change)
        self.state_manager.add_execution_state_callback(self._on_execution_state_change)
        
        logger.info("ConsoleMenuCLI initialized with advanced features")
    
    def _setup_menu(self) -> None:
        """Set up the menu options."""
        # Create main menu without default exit option
        self.menu = ConsoleMenu("MacroPosFlow - Phase 2", "Select an option:", show_exit_option=False)
        self.menu.border_style = AsciiBorderStyle()
        
        # Main menu items
        self.menu.append_item(FunctionItem("🎙️  Recording", self._show_recording_menu))
        self.menu.append_item(FunctionItem("▶️  Execution", self._show_execution_menu))
        self.menu.append_item(FunctionItem("📝 Macro Management", self._show_macro_menu))
        self.menu.append_item(FunctionItem("⚙️  Settings", self._show_settings_menu))
        self.menu.append_item(FunctionItem("📊 System Status", self._show_system_status))
        self.menu.append_item(FunctionItem("❌ Exit", self._cleanup_and_exit))
        
        # Create submenus
        self._setup_recording_submenu()
        self._setup_execution_submenu()
        self._setup_macro_submenu()
        self._setup_settings_submenu()
    
    def _setup_recording_submenu(self) -> None:
        """Set up the recording submenu."""
        self.recording_menu = ConsoleMenu("Recording Options", "Select an option:", show_exit_option=False)
        self.recording_menu.border_style = AsciiBorderStyle()
        
        self.recording_menu.append_item(FunctionItem("🔴 Start Recording Session", self._start_recording_session))
        self.recording_menu.append_item(FunctionItem("⏸️  Pause/Resume Recording", self._toggle_recording_pause))
        self.recording_menu.append_item(FunctionItem("⏹️  Stop Recording", self._stop_recording_session))
        self.recording_menu.append_item(FunctionItem("📋 List Recorded Actions", self._list_recorded_actions))
        self.recording_menu.append_item(FunctionItem("🗑️  Clear Recorded Actions", self._clear_recorded_actions))
        self.recording_menu.append_item(FunctionItem("⬅️  Back to Main Menu", self._back_to_main))
        
        # Add to main menu as submenu
        self.recording_submenu_item = SubmenuItem("🎙️  Recording", self.recording_menu, self.menu)
        self.menu.append_item(self.recording_submenu_item)
    
    def _setup_execution_submenu(self) -> None:
        """Set up the execution submenu."""
        self.execution_menu = ConsoleMenu("Execution Options", "Select an option:", show_exit_option=False)
        self.execution_menu.border_style = AsciiBorderStyle()
        
        self.execution_menu.append_item(FunctionItem("▶️  Run Current Sequence", self._run_current_sequence))
        self.execution_menu.append_item(FunctionItem("⏸️  Pause/Resume Execution", self._toggle_execution_pause))
        self.execution_menu.append_item(FunctionItem("⏹️  Stop Execution", self._stop_execution))
        self.execution_menu.append_item(FunctionItem("🔄 Set Loop Count", self._set_loop_count))
        self.execution_menu.append_item(FunctionItem("🎭 Toggle Dry Run Mode", self._toggle_dry_run))
        self.execution_menu.append_item(FunctionItem("⬅️  Back to Main Menu", self._back_to_main))
        
        # Add to main menu as submenu
        self.execution_submenu_item = SubmenuItem("▶️  Execution", self.execution_menu, self.menu)
        self.menu.append_item(self.execution_submenu_item)
    
    def _setup_macro_submenu(self) -> None:
        """Set up the macro management submenu."""
        self.macro_menu = ConsoleMenu("Macro Management", "Select an option:", show_exit_option=False)
        self.macro_menu.border_style = AsciiBorderStyle()
        
        self.macro_menu.append_item(FunctionItem("💾 Save Macro", self._save_macro))
        self.macro_menu.append_item(FunctionItem("📁 Load Macro", self._load_macro))
        self.macro_menu.append_item(FunctionItem("📋 List Available Macros", self._list_available_macros))
        self.macro_menu.append_item(FunctionItem("🗑️  Delete Macro", self._delete_macro))
        self.macro_menu.append_item(FunctionItem("⬅️  Back to Main Menu", self._back_to_main))
        
        # Add to main menu as submenu
        self.macro_submenu_item = SubmenuItem("📝 Macro Management", self.macro_menu, self.menu)
        self.menu.append_item(self.macro_submenu_item)
    
    def _setup_settings_submenu(self) -> None:
        """Set up the settings submenu."""
        self.settings_menu = ConsoleMenu("Settings", "Select an option:", show_exit_option=False)
        self.settings_menu.border_style = AsciiBorderStyle()
        
        self.settings_menu.append_item(FunctionItem("🔑 View Key Bindings", self._view_key_bindings))
        self.settings_menu.append_item(FunctionItem("⚙️  View Execution Settings", self._view_execution_settings))
        self.settings_menu.append_item(FunctionItem("🎙️  View Recording Settings", self._view_recording_settings))
        self.settings_menu.append_item(FunctionItem("🖥️  View UI Settings", self._view_ui_settings))
        self.settings_menu.append_item(FunctionItem("🔄 Reset to Defaults", self._reset_settings))
        self.settings_menu.append_item(FunctionItem("⬅️  Back to Main Menu", self._back_to_main))
        
        # Add to main menu as submenu
        self.settings_submenu_item = SubmenuItem("⚙️  Settings", self.settings_menu, self.menu)
        self.menu.append_item(self.settings_submenu_item)
    
    def run(self) -> None:
        """
        Run the CLI menu loop.
        
        This method displays the menu and handles user interactions.
        """
        logger.info("Starting CLI menu")
        
        print("🎯 MacroPosFlow - Phase 2 Advanced")
        print("=" * 50)
        print("🔧 Advanced Features:")
        print("  • State management (Stopped/Running/Paused)")
        print("  • Configurable key bindings")
        print("  • Loop execution support")
        print("  • Enhanced recording and execution")
        print("  • Settings management")
        print()
        print("⌨️  Default Key Bindings:")
        key_bindings = self.settings_manager.get_key_bindings()
        print(f"  • Start/Stop Recording: {'+'.join(key_bindings.record_start_stop)}")
        print(f"  • Pause/Resume Recording: {'+'.join(key_bindings.record_pause_resume)}")
        print(f"  • Record Position: {'+'.join(key_bindings.record_position)}")
        print(f"  • Alternative Click: {'+'.join(key_bindings.record_alt_click)}")
        print(f"  • Start/Stop Execution: {'+'.join(key_bindings.execute_start_stop)}")
        print(f"  • Pause/Resume Execution: {'+'.join(key_bindings.execute_pause_resume)}")
        print(f"  • Emergency Kill: {'+'.join(key_bindings.execute_kill)}")
        print(f"  • Global Emergency Stop: {'+'.join(key_bindings.global_emergency_stop)}")
        print("=" * 50)
        
        # Show the menu and let it handle the loop
        try:
            self.menu.show()
            self._cleanup()
            logger.info("Application exited normally")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self._cleanup()
        except Exception as e:
            logger.error(f"Error in menu: {e}")
            print(f"Error: {e}")
            self._cleanup()
    
    def _cleanup_and_exit(self) -> None:
        """Clean up resources and exit the application."""
        self._cleanup()
        logger.info("Exiting application")
        # This will exit the menu loop
        raise SystemExit(0)
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Stop recording if active
            if self.state_manager.is_recording_active():
                self.recorder.stop_recording()
            
            # Stop execution if active
            if self.state_manager.is_execution_active():
                self.executor.stop_execution()
            
            # Reset all states
            self.state_manager.reset_all_states()
            
            logger.info("CLI cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _show_recording_menu(self) -> None:
        """Show recording submenu."""
        self.recording_menu.show()
    
    def _show_execution_menu(self) -> None:
        """Show execution submenu."""
        self.execution_menu.show()
    
    def _show_macro_menu(self) -> None:
        """Show macro management submenu."""
        self.macro_menu.show()
    
    def _show_settings_menu(self) -> None:
        """Show settings submenu."""
        self.settings_menu.show()
    
    def _back_to_main(self) -> None:
        """Return to main menu."""
        pass
    
    def _start_recording_session(self) -> None:
        """Start recording session - prepares for recording but doesn't start immediately."""
        if self.state_manager.is_recording_active():
            print("⚠️  Recording is already active!")
            input("Press Enter to continue...")
            return
        
        if self.state_manager.is_execution_active():
            print("⚠️  Cannot start recording while executing!")
            input("Press Enter to continue...")
            return
        
        print("\n🔴 Recording Session Initialized")
        print("=" * 40)
        print("📋 Recording is now READY but not started.")
        print()
        print("⌨️  Use the following hotkeys to control recording:")
        key_bindings = self.settings_manager.get_key_bindings()
        print(f"  • Start Recording: {'+'.join(key_bindings.record_start_stop)}")
        print(f"  • Pause/Resume: {'+'.join(key_bindings.record_pause_resume)}")
        print(f"  • Record Position: {'+'.join(key_bindings.record_position)}")
        print(f"  • Alternative Click: {'+'.join(key_bindings.record_alt_click)}")
        print(f"  • Emergency Stop: {'+'.join(key_bindings.global_emergency_stop)}")
        print()
        print("🖱️  Mouse actions will be recorded when recording is active:")
        print("  • Click normally to record clicks")
        print("  • Use position hotkey to record mouse position without clicking")
        print("  • Use alternative click hotkey for special click recording")
        print()
        print("⏳ Waiting for you to press the start recording hotkey...")
        print("Press Enter to return to menu...")
        
        # Initialize recording system
        self.recorder.start_recording()
        
        input()
    
    def _toggle_recording_pause(self) -> None:
        """Toggle recording pause/resume."""
        if not self.state_manager.is_recording_active():
            print("⚠️  No recording session active!")
            input("Press Enter to continue...")
            return
        
        if self.state_manager.is_recording_paused():
            if self.recorder.resume_recording():
                print("▶️  Recording resumed!")
            else:
                print("❌ Failed to resume recording!")
        elif self.state_manager.is_recording_running():
            if self.recorder.pause_recording():
                print("⏸️  Recording paused!")
            else:
                print("❌ Failed to pause recording!")
        
        input("Press Enter to continue...")
    
    def _stop_recording_session(self) -> None:
        """Stop recording session."""
        if not self.state_manager.is_recording_active():
            print("⚠️  No recording session active!")
            input("Press Enter to continue...")
            return
        
        print("\n⏹️  Stopping recording session...")
        
        # Stop recording and get actions
        recorded_actions = self.recorder.stop_recording()
        
        # Add to current actions
        self.current_actions.extend(recorded_actions)
        
        print(f"✅ Recording stopped!")
        print(f"📊 Total actions recorded: {len(recorded_actions)}")
        print(f"📊 Total actions in sequence: {len(self.current_actions)}")
        
        # Show recording summary
        if recorded_actions:
            print("\n📝 Recording Summary:")
            print("-" * 30)
            action_types = {}
            for action in recorded_actions:
                action_type = action.get('type', 'unknown')
                action_types[action_type] = action_types.get(action_type, 0) + 1
            
            for action_type, count in action_types.items():
                print(f"  {action_type}: {count}")
            print("-" * 30)
        
        input("Press Enter to continue...")
    
    def _list_recorded_actions(self) -> None:
        """List all recorded actions."""
        if not self.current_actions:
            print("\n📝 No recorded actions yet.")
            print("Use 'Start Recording Session' to start recording.")
            input("Press Enter to continue...")
            return
        
        print(f"\n📝 Recorded Actions ({len(self.current_actions)} actions):")
        print("-" * 60)
        
        total_time = 0.0
        for i, action in enumerate(self.current_actions, 1):
            action_type = action.get('type', 'unknown')
            delay = action.get('delay', 0.0)
            total_time += delay
            
            if action_type == 'click':
                x = action.get('abs_x', 0)
                y = action.get('abs_y', 0)
                button = action.get('button', 'unknown')
                recorded_via = action.get('recorded_via_hotkey', False)
                alt_click = action.get('recorded_via_alt_hotkey', False)
                
                via_info = ""
                if recorded_via:
                    via_info = " (via hotkey)"
                elif alt_click:
                    via_info = " (alt click)"
                
                print(f"{i:2d}. Click at ({x:4d}, {y:4d}) with {button} button{via_info} (delay: {delay:.2f}s)")
            
            elif action_type == 'wait':
                seconds = action.get('seconds', 0.0)
                print(f"{i:2d}. Wait {seconds:.2f} seconds")
            
            elif action_type == 'keypress':
                key = action.get('key', 'unknown')
                is_combination = action.get('is_combination', False)
                if is_combination:
                    print(f"{i:2d}. Key combination: {key} (delay: {delay:.2f}s)")
                else:
                    print(f"{i:2d}. Press '{key}' key (delay: {delay:.2f}s)")
            
            elif action_type == 'scroll':
                dx = action.get('dx', 0)
                dy = action.get('dy', 0)
                print(f"{i:2d}. Scroll (dx: {dx}, dy: {dy}) (delay: {delay:.2f}s)")
            
            else:
                print(f"{i:2d}. {action_type}: {action} (delay: {delay:.2f}s)")
        
        print("-" * 60)
        print(f"⏱️  Total sequence time: {total_time:.2f} seconds")
        print(f"🎯 Average delay per action: {total_time/max(1, len(self.current_actions)):.2f} seconds")
        
        input("Press Enter to continue...")
    
    def _clear_recorded_actions(self) -> None:
        """Clear all recorded actions."""
        if not self.current_actions:
            print("\n📝 No recorded actions to clear.")
            input("Press Enter to continue...")
            return
        
        ui_settings = self.settings_manager.get_ui_settings()
        if ui_settings.confirm_destructive_actions:
            confirm = input("\n⚠️  Are you sure you want to clear all recorded actions? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("❌ Operation cancelled.")
                input("Press Enter to continue...")
                return
        
        self.current_actions.clear()
        self.recorder.clear_actions()
        print("✅ All recorded actions cleared.")
        
        input("Press Enter to continue...")
    
    def _run_current_sequence(self) -> None:
        """Run the current sequence of actions."""
        if not self.current_actions:
            print("\n📝 No recorded actions to run.")
            print("Record some actions first or load a macro.")
            input("Press Enter to continue...")
            return
        
        if self.state_manager.is_execution_active():
            print("⚠️  Execution is already active!")
            input("Press Enter to continue...")
            return
        
        if self.state_manager.is_recording_active():
            print("⚠️  Cannot execute while recording!")
            input("Press Enter to continue...")
            return
        
        # Get execution settings
        execution_settings = self.settings_manager.get_execution_settings()
        loop_count = execution_settings.default_loop_count
        
        print(f"\n▶️  Execution Setup")
        print("-" * 30)
        print(f"📊 Actions to execute: {len(self.current_actions)}")
        print(f"🔄 Loop count: {loop_count}")
        print(f"🎭 Mode: {'DRY RUN' if self.executor.dry_run else 'LIVE'}")
        print()
        
        # Allow user to modify loop count
        try:
            user_loop_count = input(f"Enter loop count (default: {loop_count}): ").strip()
            if user_loop_count:
                loop_count = max(1, int(user_loop_count))
        except ValueError:
            print(f"⚠️  Invalid input, using default: {loop_count}")
        
        print(f"\n🚀 Starting execution with {loop_count} loop(s)...")
        print("⌨️  Use hotkeys to control execution:")
        key_bindings = self.settings_manager.get_key_bindings()
        print(f"  • Start/Stop: {'+'.join(key_bindings.execute_start_stop)}")
        print(f"  • Pause/Resume: {'+'.join(key_bindings.execute_pause_resume)}")
        print(f"  • Emergency Kill: {'+'.join(key_bindings.execute_kill)}")
        print(f"  • Global Emergency Stop: {'+'.join(key_bindings.global_emergency_stop)}")
        print()
        
        # Confirm execution
        ui_settings = self.settings_manager.get_ui_settings()
        if ui_settings.confirm_destructive_actions:
            confirm = input("Press Enter to start execution (or 'c' to cancel): ").strip().lower()
            if confirm == 'c':
                print("❌ Execution cancelled.")
                return
        
        # Start execution
        success = self.executor.execute_actions(self.current_actions, loop_count)
        
        if success:
            print("\n🎉 Execution completed successfully!")
        else:
            print("\n⚠️  Execution was stopped or failed")
        
        input("Press Enter to continue...")
    
    def _toggle_execution_pause(self) -> None:
        """Toggle execution pause/resume."""
        if not self.state_manager.is_execution_active():
            print("⚠️  No execution active!")
            input("Press Enter to continue...")
            return
        
        if self.state_manager.is_execution_paused():
            if self.executor.resume_execution():
                print("▶️  Execution resumed!")
            else:
                print("❌ Failed to resume execution!")
        elif self.state_manager.is_execution_running():
            if self.executor.pause_execution():
                print("⏸️  Execution paused!")
            else:
                print("❌ Failed to pause execution!")
        
        input("Press Enter to continue...")
    
    def _stop_execution(self) -> None:
        """Stop execution."""
        if not self.state_manager.is_execution_active():
            print("⚠️  No execution active!")
            input("Press Enter to continue...")
            return
        
        print("\n⏹️  Stopping execution...")
        
        if self.executor.stop_execution():
            print("✅ Execution stopped!")
        else:
            print("❌ Failed to stop execution!")
        
        input("Press Enter to continue...")
    
    def _set_loop_count(self) -> None:
        """Set default loop count for execution."""
        execution_settings = self.settings_manager.get_execution_settings()
        current_count = execution_settings.default_loop_count
        
        print(f"\n🔄 Set Default Loop Count")
        print("-" * 30)
        print(f"Current default loop count: {current_count}")
        
        try:
            new_count = input("Enter new default loop count (1-999): ").strip()
            if new_count:
                count = int(new_count)
                if 1 <= count <= 999:
                    execution_settings.default_loop_count = count
                    if self.settings_manager.update_execution_settings(execution_settings):
                        print(f"✅ Default loop count set to {count}")
                    else:
                        print("❌ Failed to update settings!")
                else:
                    print("❌ Loop count must be between 1 and 999!")
            else:
                print("❌ No input provided!")
        except ValueError:
            print("❌ Please enter a valid number!")
        
        input("Press Enter to continue...")
    
    def _toggle_dry_run(self) -> None:
        """Toggle dry run mode."""
        current_mode = self.executor.dry_run
        new_mode = not current_mode
        self.executor.set_dry_run(new_mode)
        
        print(f"\n🎭 Dry Run Mode: {'ON' if new_mode else 'OFF'}")
        if new_mode:
            print("Actions will be printed but not executed.")
        else:
            print("Actions will be executed normally.")
        
        input("Press Enter to continue...")
    
    def _save_macro(self) -> None:
        """Save the current sequence as a macro."""
        if not self.current_actions:
            print("\n📝 No recorded actions to save.")
            return
        
        print("\n💾 Save Macro")
        print("-" * 20)
        
        # Get macro name
        default_name = self.current_macro_name or f"macro_{int(time.time())}"
        macro_name = input(f"Enter macro name (default: {default_name}): ").strip()
        
        if not macro_name:
            macro_name = default_name
        
        # Get description
        description = input("Enter description (optional): ").strip()
        
        # Create metadata
        metadata = {
            'name': macro_name,
            'description': description,
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'author': 'MacroPosFlow User',
            'version': '2.0',
            'action_count': len(self.current_actions),
            'total_duration': sum(action.get('delay', 0) for action in self.current_actions)
        }
        
        # Save the macro
        if self.config_manager.save_macro(self.current_actions, macro_name, metadata):
            print(f"✅ Macro '{macro_name}' saved successfully!")
            self.current_macro_name = macro_name
        else:
            print(f"❌ Failed to save macro '{macro_name}'.")
        
        input("Press Enter to continue...")
    
    def _load_macro(self) -> None:
        """Load a macro from file."""
        macros = self.config_manager.list_macros()
        
        if not macros:
            print("\n📁 No saved macros found.")
            return
        
        print("\n📁 Available Macros:")
        print("-" * 30)
        
        for i, macro_name in enumerate(macros, 1):
            info = self.config_manager.get_macro_info(macro_name)
            if info:
                action_count = info.get('action_count', 0)
                description = info.get('description', 'No description')
                created = info.get('created', 'Unknown')
                print(f"{i:2d}. {macro_name}")
                print(f"     Actions: {action_count}")
                print(f"     Description: {description}")
                print(f"     Created: {created}")
                print()
            else:
                print(f"{i:2d}. {macro_name}")
        
        print("-" * 30)
        
        try:
            choice = input("Enter macro number to load (or 0 to cancel): ").strip()
            if choice == '0':
                return
            
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(macros):
                macro_name = macros[choice_num]
                config = self.config_manager.load_macro(macro_name)
                
                if config:
                    self.current_actions = config.get('actions', [])
                    self.current_macro_name = macro_name
                    print(f"✅ Loaded macro '{macro_name}' with {len(self.current_actions)} actions.")
                else:
                    print(f"❌ Failed to load macro '{macro_name}'.")
            else:
                print("❌ Invalid macro number.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        except Exception as e:
            logger.error(f"Error loading macro: {e}")
            print(f"❌ Error: {e}")
        
        input("Press Enter to continue...")
    
    def _list_available_macros(self) -> None:
        """List all available macros."""
        macros = self.config_manager.list_macros()
        
        if not macros:
            print("\n📁 No saved macros found.")
            return
        
        print(f"\n📁 Available Macros ({len(macros)}):")
        print("-" * 50)
        
        for macro_name in macros:
            info = self.config_manager.get_macro_info(macro_name)
            if info:
                action_count = info.get('action_count', 0)
                description = info.get('description', 'No description')
                created = info.get('created', 'Unknown')
                file_size = info.get('file_size', 0)
                version = info.get('version', 'Unknown')
                
                print(f"📄 {macro_name} (v{version})")
                print(f"   Actions: {action_count}")
                print(f"   Description: {description}")
                print(f"   Created: {created}")
                print(f"   Size: {file_size} bytes")
                print()
        
        print("-" * 50)
        input("Press Enter to continue...")
    
    def _delete_macro(self) -> None:
        """Delete a macro file."""
        macros = self.config_manager.list_macros()
        
        if not macros:
            print("\n📁 No saved macros found.")
            return
        
        print("\n🗑️  Delete Macro")
        print("-" * 20)
        
        for i, macro_name in enumerate(macros, 1):
            print(f"{i}. {macro_name}")
        
        print("0. Cancel")
        print("-" * 20)
        
        try:
            choice = input("Enter macro number to delete: ").strip()
            if choice == '0':
                return
            
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(macros):
                macro_name = macros[choice_num]
                
                # Confirm deletion
                ui_settings = self.settings_manager.get_ui_settings()
                if ui_settings.confirm_destructive_actions:
                    confirm = input(f"⚠️  Are you sure you want to delete '{macro_name}'? (y/N): ")
                    if confirm.lower() not in ['y', 'yes']:
                        print("❌ Deletion cancelled.")
                        input("Press Enter to continue...")
                        return
                
                if self.config_manager.delete_macro(macro_name):
                    print(f"✅ Macro '{macro_name}' deleted.")
                else:
                    print(f"❌ Failed to delete macro '{macro_name}'.")
            else:
                print("❌ Invalid macro number.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        except Exception as e:
            logger.error(f"Error deleting macro: {e}")
            print(f"❌ Error: {e}")
        
        input("Press Enter to continue...")
    
    def _view_key_bindings(self) -> None:
        """View current key bindings."""
        key_bindings = self.settings_manager.get_key_bindings()
        
        print("\n🔑 Current Key Bindings")
        print("=" * 40)
        
        print("🎙️  Recording Controls:")
        print(f"  Start/Stop Recording: {'+'.join(key_bindings.record_start_stop)}")
        print(f"  Pause/Resume Recording: {'+'.join(key_bindings.record_pause_resume)}")
        print(f"  Record Position: {'+'.join(key_bindings.record_position)}")
        print(f"  Alternative Click: {'+'.join(key_bindings.record_alt_click)}")
        print()
        
        print("▶️  Execution Controls:")
        print(f"  Start/Stop Execution: {'+'.join(key_bindings.execute_start_stop)}")
        print(f"  Pause/Resume Execution: {'+'.join(key_bindings.execute_pause_resume)}")
        print(f"  Emergency Kill: {'+'.join(key_bindings.execute_kill)}")
        print()
        
        print("🌐 Global Controls:")
        print(f"  Emergency Stop: {'+'.join(key_bindings.global_emergency_stop)}")
        print("=" * 40)
        
        input("Press Enter to continue...")
    
    def _view_execution_settings(self) -> None:
        """View execution settings."""
        execution_settings = self.settings_manager.get_execution_settings()
        
        print("\n⚙️  Execution Settings")
        print("=" * 40)
        print(f"🔄 Default Loop Count: {execution_settings.default_loop_count}")
        print(f"⏱️  Default Delay: {execution_settings.default_delay}s")
        print(f"🎲 Enable Randomness: {execution_settings.enable_randomness}")
        print(f"🎯 Randomness Radius: {execution_settings.randomness_radius}px")
        print(f"🌊 Enable Smoothing: {execution_settings.enable_smoothing}")
        print(f"⏱️  Smoothing Duration: {execution_settings.smoothing_duration}s")
        print("=" * 40)
        
        input("Press Enter to continue...")
    
    def _view_recording_settings(self) -> None:
        """View recording settings."""
        recording_settings = self.settings_manager.get_recording_settings()
        
        print("\n🎙️  Recording Settings")
        print("=" * 40)
        print(f"⏱️  Default Delay: {recording_settings.default_delay}s")
        print(f"⏰ Auto Timestamp: {recording_settings.enable_auto_timestamp}")
        print(f"👁️  Real-time Feedback: {recording_settings.show_real_time_feedback}")
        print("=" * 40)
        
        input("Press Enter to continue...")
    
    def _view_ui_settings(self) -> None:
        """View UI settings."""
        ui_settings = self.settings_manager.get_ui_settings()
        
        print("\n🖥️  UI Settings")
        print("=" * 40)
        print(f"📊 Show Action Count: {ui_settings.show_action_count}")
        print(f"⏱️  Show Timing Info: {ui_settings.show_timing_info}")
        print(f"⚠️  Confirm Destructive Actions: {ui_settings.confirm_destructive_actions}")
        print(f"📝 Verbose Logging: {ui_settings.verbose_logging}")
        print("=" * 40)
        
        input("Press Enter to continue...")
    
    def _reset_settings(self) -> None:
        """Reset settings to default values."""
        print("\n🔄 Reset Settings to Defaults")
        print("-" * 30)
        
        ui_settings = self.settings_manager.get_ui_settings()
        if ui_settings.confirm_destructive_actions:
            confirm = input("⚠️  Are you sure you want to reset all settings to defaults? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("❌ Reset cancelled.")
                input("Press Enter to continue...")
                return
        
        if self.settings_manager.reset_to_defaults():
            print("✅ Settings reset to defaults!")
        else:
            print("❌ Failed to reset settings!")
        
        input("Press Enter to continue...")
    
    def _show_system_status(self) -> None:
        """Show system status."""
        status = self.state_manager.get_system_status()
        
        print("\n📊 System Status")
        print("=" * 50)
        
        print("🎙️  Recording Status:")
        print(f"  State: {status['recording_state'].upper()}")
        print(f"  Duration: {status['recording_duration']:.2f}s")
        print(f"  Actions: {status['recording_actions']}")
        print(f"  Loops: {status['recording_loops']}")
        print()
        
        print("▶️  Execution Status:")
        print(f"  State: {status['execution_state'].upper()}")
        print(f"  Duration: {status['execution_duration']:.2f}s")
        print(f"  Actions: {status['execution_actions']}")
        print(f"  Loops: {status['execution_loops']}")
        print()
        
        print("🎮 Available Actions:")
        print(f"  Can Start Recording: {status['can_start_recording']}")
        print(f"  Can Pause Recording: {status['can_pause_recording']}")
        print(f"  Can Resume Recording: {status['can_resume_recording']}")
        print(f"  Can Stop Recording: {status['can_stop_recording']}")
        print(f"  Can Start Execution: {status['can_start_execution']}")
        print(f"  Can Pause Execution: {status['can_pause_execution']}")
        print(f"  Can Resume Execution: {status['can_resume_execution']}")
        print(f"  Can Stop Execution: {status['can_stop_execution']}")
        print()
        
        print("📋 Current Session:")
        print(f"  Actions in Memory: {len(self.current_actions)}")
        print(f"  Current Macro: {self.current_macro_name or 'None'}")
        print(f"  Dry Run Mode: {'ON' if self.executor.dry_run else 'OFF'}")
        print("=" * 50)
        
        input("Press Enter to continue...")
    
    def _on_action_recorded(self, action: Dict[str, Any]) -> None:
        """Callback when an action is recorded."""
        self.current_actions.append(action)
        
        # Provide feedback to the user if enabled
        recording_settings = self.settings_manager.get_recording_settings()
        if recording_settings.show_real_time_feedback:
            action_type = action.get('type', 'unknown')
            
            if action_type == 'click':
                x = action.get('abs_x', 0)
                y = action.get('abs_y', 0)
                button = action.get('button', 'unknown')
                recorded_via = action.get('recorded_via_hotkey', False)
                alt_click = action.get('recorded_via_alt_hotkey', False)
                
                if recorded_via:
                    print(f"📍 Recorded position at ({x}, {y}) via hotkey")
                elif alt_click:
                    print(f"📍 Recorded alternative click at ({x}, {y})")
                else:
                    print(f"📍 Recorded click at ({x}, {y}) with {button} button")
            
            elif action_type == 'keypress':
                key = action.get('key', 'unknown')
                is_combination = action.get('is_combination', False)
                if is_combination:
                    print(f"⌨️  Recorded key combination: {key}")
                else:
                    print(f"⌨️  Recorded keypress: {key}")
            
            elif action_type == 'scroll':
                dx = action.get('dx', 0)
                dy = action.get('dy', 0)
                print(f"🖱️  Recorded scroll (dx: {dx}, dy: {dy})")
    
    def _on_action_start(self, action: Dict[str, Any]) -> None:
        """Callback when an action starts execution."""
        action_type = action.get('type', 'unknown')
        
        if action_type == 'click':
            x = action.get('abs_x', 0)
            y = action.get('abs_y', 0)
            button = action.get('button', 'unknown')
            print(f"▶️  Clicking at ({x}, {y}) with {button} button...")
        
        elif action_type == 'wait':
            seconds = action.get('seconds', 0.0)
            print(f"⏱️  Waiting {seconds:.2f} seconds...")
        
        elif action_type == 'keypress':
            key = action.get('key', 'unknown')
            is_combination = action.get('is_combination', False)
            if is_combination:
                print(f"⌨️  Pressing combination: {key}...")
            else:
                print(f"⌨️  Pressing key: {key}...")
        
        elif action_type == 'scroll':
            dx = action.get('dx', 0)
            dy = action.get('dy', 0)
            print(f"🖱️  Scrolling (dx: {dx}, dy: {dy})...")
    
    def _on_action_complete(self, action: Dict[str, Any]) -> None:
        """Callback when an action completes execution."""
        action_type = action.get('type', 'unknown')
        print(f"✅ {action_type.title()} completed")
    
    def _on_execution_start(self) -> None:
        """Callback when execution starts."""
        print("🚀 Execution started")
    
    def _on_execution_complete(self, success: bool) -> None:
        """Callback when execution completes."""
        if success:
            print("🎉 Execution completed successfully!")
        else:
            print("⚠️  Execution stopped or failed")
    
    def _on_execution_error(self, error: Exception) -> None:
        """Callback when execution encounters an error."""
        print(f"❌ Execution error: {error}")
    
    def _on_loop_start(self, loop_number: int) -> None:
        """Callback when each loop starts."""
        execution_settings = self.settings_manager.get_execution_settings()
        total_loops = execution_settings.default_loop_count
        print(f"🔄 Starting loop {loop_number}/{total_loops}")
    
    def _on_loop_complete(self, loop_number: int) -> None:
        """Callback when each loop completes."""
        execution_settings = self.settings_manager.get_execution_settings()
        total_loops = execution_settings.default_loop_count
        print(f"✅ Loop {loop_number}/{total_loops} completed")
    
    def _on_recording_state_change(self, old_state: ProcessState, new_state: ProcessState) -> None:
        """Callback when recording state changes."""
        if new_state == ProcessState.RUNNING:
            print("🎙️  Recording started!")
        elif new_state == ProcessState.PAUSED:
            print("⏸️  Recording paused!")
        elif new_state == ProcessState.STOPPED:
            print("⏹️  Recording stopped!")
    
    def _on_execution_state_change(self, old_state: ProcessState, new_state: ProcessState) -> None:
        """Callback when execution state changes."""
        if new_state == ProcessState.RUNNING:
            print("▶️  Execution started!")
        elif new_state == ProcessState.PAUSED:
            print("⏸️  Execution paused!")
        elif new_state == ProcessState.STOPPED:
            print("⏹️  Execution stopped!")