"""
Executor module for MacroPosFlow.

This module provides functionality to execute recorded action sequences
with proper timing, emergency stop functionality, loop support, and state management.
"""

import threading
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from pynput import mouse, keyboard
from pynput.keyboard import KeyCode, Key
import pyautogui

from .settings import SettingsManager, ExecutionSettings
from .state_manager import StateManager, ProcessState

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes recorded action sequences with advanced features.
    
    This class provides functionality to replay recorded actions with proper timing,
    delays, emergency stop capability, loop support, and state management.
    """
    
    def __init__(self, 
                 settings_manager: Optional[SettingsManager] = None,
                 state_manager: Optional[StateManager] = None,
                 dry_run: bool = False):
        """
        Initialize the ActionExecutor.
        
        Args:
            settings_manager: Settings manager for configuration
            state_manager: State manager for state management
            dry_run: If True, actions are printed but not executed
        """
        self.settings_manager = settings_manager or SettingsManager()
        self.state_manager = state_manager or StateManager()
        self.dry_run = dry_run
        
        # Execution state
        self.is_executing = False
        self.execution_thread: Optional[threading.Thread] = None
        self.current_actions: List[Dict[str, Any]] = []
        self.loop_count = 1
        self.current_loop = 1
        self.current_action_index = 0
        self.pause_start_time = 0.0
        
        # Threading locks
        self.execution_lock = threading.Lock()
        self.pause_event = threading.Event()
        
        # Action handlers
        self.action_handlers = {
            'click': self._handle_click,
            'wait': self._handle_wait,
            'keypress': self._handle_keypress,
            'scroll': self._handle_scroll
        }
        
        # Callbacks
        self.on_action_start: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_action_complete: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_execution_start: Optional[Callable[[], None]] = None
        self.on_execution_complete: Optional[Callable[[bool], None]] = None
        self.on_execution_error: Optional[Callable[[Exception], None]] = None
        self.on_loop_start: Optional[Callable[[int], None]] = None
        self.on_loop_complete: Optional[Callable[[int], None]] = None
        
        # Set up state change callbacks
        self.state_manager.add_execution_state_callback(self._on_execution_state_change)
        
        logger.info(f"ActionExecutor initialized (dry_run={dry_run})")
    
    def execute_actions(self, actions: List[Dict[str, Any]], loop_count: int = 1) -> bool:
        """
        Execute a sequence of actions.
        
        Args:
            actions: List of actions to execute
            loop_count: Number of times to repeat the sequence (default: 1)
            
        Returns:
            True if execution completed successfully, False if stopped or failed
        """
        if self.is_executing:
            logger.warning("Execution already in progress")
            return False
        
        if not actions:
            logger.warning("No actions to execute")
            return False
        
        with self.execution_lock:
            self.current_actions = actions
            self.loop_count = max(1, loop_count)
            self.current_loop = 1
            self.current_action_index = 0
            self.pause_start_time = 0.0
            self.pause_event.clear()
            
            # Update execution info
            self.state_manager.update_execution_info(
                action_count=len(actions),
                loop_count=self.loop_count,
                current_loop=self.current_loop,
                current_action_index=self.current_action_index
            )
            
            # Start execution in a separate thread
            self.execution_thread = threading.Thread(
                target=self._execute_actions_thread,
                daemon=True
            )
            self.execution_thread.start()
            
            logger.info(f"Started execution of {len(actions)} actions with {loop_count} loops")
            return True
    
    def execute_actions_sync(self, actions: List[Dict[str, Any]], loop_count: int = 1) -> bool:
        """
        Execute a sequence of actions synchronously.
        
        Args:
            actions: List of actions to execute
            loop_count: Number of times to repeat the sequence (default: 1)
            
        Returns:
            True if execution completed successfully, False if stopped or failed
        """
        if self.is_executing:
            logger.warning("Execution already in progress")
            return False
        
        if not actions:
            logger.warning("No actions to execute")
            return False
        
        with self.execution_lock:
            self.current_actions = actions
            self.loop_count = max(1, loop_count)
            self.current_loop = 1
            self.current_action_index = 0
            self.pause_start_time = 0.0
            self.pause_event.clear()
            
            # Update execution info
            self.state_manager.update_execution_info(
                action_count=len(actions),
                loop_count=self.loop_count,
                current_loop=self.current_loop,
                current_action_index=self.current_action_index
            )
            
            # Start execution state
            self.state_manager.start_execution("Synchronous execution start")
            
            logger.info(f"Started synchronous execution of {len(actions)} actions with {loop_count} loops")
            
            try:
                # Execute actions synchronously
                result = self._execute_actions_internal()
                return result
                
            except Exception as e:
                logger.error(f"Error during synchronous execution: {e}")
                self.state_manager.stop_execution("Execution error")
                return False
    
    def _execute_actions_thread(self) -> None:
        """Thread function for executing actions."""
        try:
            # Start execution state
            self.state_manager.start_execution("Asynchronous execution start")
            
            # Execute actions
            result = self._execute_actions_internal()
            
            # Stop execution state
            if result:
                self.state_manager.stop_execution("Execution completed successfully")
            else:
                self.state_manager.stop_execution("Execution stopped or failed")
                
        except Exception as e:
            logger.error(f"Error in execution thread: {e}")
            self.state_manager.stop_execution("Execution error")
            
            # Call error callback
            if self.on_execution_error:
                try:
                    self.on_execution_error(e)
                except Exception as callback_error:
                    logger.error(f"Error in execution error callback: {callback_error}")
        
        finally:
            with self.execution_lock:
                self.is_executing = False
                self.execution_thread = None
    
    def _execute_actions_internal(self) -> bool:
        """
        Internal method to execute actions.
        
        Returns:
            True if execution completed successfully, False if stopped or failed
        """
        execution_success = True
        
        try:
            # Call execution start callback
            if self.on_execution_start:
                try:
                    self.on_execution_start()
                except Exception as e:
                    logger.error(f"Error in execution start callback: {e}")
            
            # Execute loops
            for loop in range(1, self.loop_count + 1):
                if not self.state_manager.is_execution_running():
                    break
                
                self.current_loop = loop
                self.current_action_index = 0
                
                # Update execution info
                self.state_manager.update_execution_info(current_loop=loop, current_action_index=0)
                
                # Call loop start callback
                if self.on_loop_start:
                    try:
                        self.on_loop_start(loop)
                    except Exception as e:
                        logger.error(f"Error in loop start callback: {e}")
                
                logger.info(f"Starting loop {loop}/{self.loop_count}")
                
                # Execute actions in this loop
                for i, action in enumerate(self.current_actions):
                    if not self.state_manager.is_execution_running():
                        break
                    
                    self.current_action_index = i
                    
                    # Update execution info
                    self.state_manager.update_execution_info(current_action_index=i)
                    
                    # Wait for pause to be cleared if paused
                    while self.state_manager.is_execution_paused():
                        self.pause_event.wait(0.1)  # Check every 100ms
                    
                    # Check if execution is still running
                    if not self.state_manager.is_execution_running():
                        break
                    
                    # Call action start callback
                    if self.on_action_start:
                        try:
                            self.on_action_start(action)
                        except Exception as e:
                            logger.error(f"Error in action start callback: {e}")
                    
                    # Execute the action
                    success = self._execute_action(action)
                    
                    # Call action complete callback
                    if self.on_action_complete:
                        try:
                            self.on_action_complete(action)
                        except Exception as e:
                            logger.error(f"Error in action complete callback: {e}")
                    
                    if not success:
                        logger.error(f"Failed to execute action {i + 1}: {action}")
                        execution_success = False
                        break
                    
                    logger.debug(f"Executed action {i + 1}/{len(self.current_actions)}: {action['type']}")
                
                # Call loop complete callback
                if self.on_loop_complete:
                    try:
                        self.on_loop_complete(loop)
                    except Exception as e:
                        logger.error(f"Error in loop complete callback: {e}")
                
                # Small delay between loops
                if loop < self.loop_count and self.state_manager.is_execution_running():
                    time.sleep(0.1)
            
            execution_success = self.state_manager.is_execution_running()
            
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            execution_success = False
            
            # Call execution error callback
            if self.on_execution_error:
                try:
                    self.on_execution_error(e)
                except Exception as callback_error:
                    logger.error(f"Error in execution error callback: {callback_error}")
        
        finally:
            # Call execution complete callback
            if self.on_execution_complete:
                try:
                    self.on_execution_complete(execution_success)
                except Exception as e:
                    logger.error(f"Error in execution complete callback: {e}")
        
        logger.info(f"Execution completed (success={execution_success}, loops_completed={self.current_loop}/{self.loop_count})")
        return execution_success
    
    def pause_execution(self) -> bool:
        """
        Pause the current execution.
        
        Returns:
            True if pause was successful, False otherwise
        """
        if not self.state_manager.is_execution_running():
            logger.warning("Cannot pause - execution is not running")
            return False
        
        self.pause_start_time = time.time()
        self.state_manager.pause_execution("User request")
        logger.info("Execution paused")
        return True
    
    def resume_execution(self) -> bool:
        """
        Resume execution from paused state.
        
        Returns:
            True if resume was successful, False otherwise
        """
        if not self.state_manager.is_execution_paused():
            logger.warning("Cannot resume - execution is not paused")
            return False
        
        # Clear pause event to resume execution
        self.pause_event.set()
        self.pause_event.clear()
        
        # Adjust timing to account for pause duration
        if self.pause_start_time > 0:
            pause_duration = time.time() - self.pause_start_time
            # We don't need to adjust timing for execution as we use real-time delays
            self.pause_start_time = 0.0
        
        self.state_manager.resume_execution("User request")
        logger.info("Execution resumed")
        return True
    
    def stop_execution(self) -> bool:
        """
        Stop the current execution.
        
        Returns:
            True if stop was successful, False otherwise
        """
        if not self.state_manager.is_execution_active():
            logger.warning("Cannot stop - execution is not active")
            return False
        
        # Set pause event to break out of pause wait
        self.pause_event.set()
        
        # Stop execution state
        self.state_manager.stop_execution("User request")
        
        # Wait for execution thread to finish
        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_thread.join(timeout=5.0)
            if self.execution_thread.is_alive():
                logger.warning("Execution thread did not stop gracefully")
        
        logger.info("Execution stopped")
        return True
    
    def is_executing_actions(self) -> bool:
        """Check if actions are currently being executed."""
        return self.state_manager.is_execution_active()
    
    def get_execution_progress(self) -> Dict[str, Any]:
        """
        Get current execution progress information.
        
        Returns:
            Dictionary with progress information
        """
        with self.execution_lock:
            return {
                'is_executing': self.state_manager.is_execution_active(),
                'is_running': self.state_manager.is_execution_running(),
                'is_paused': self.state_manager.is_execution_paused(),
                'total_actions': len(self.current_actions),
                'current_action_index': self.current_action_index,
                'total_loops': self.loop_count,
                'current_loop': self.current_loop,
                'progress_percentage': self._calculate_progress()
            }
    
    def _calculate_progress(self) -> float:
        """
        Calculate execution progress percentage.
        
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        if not self.current_actions or self.loop_count == 0:
            return 0.0
        
        total_actions = len(self.current_actions) * self.loop_count
        completed_actions = (self.current_loop - 1) * len(self.current_actions) + self.current_action_index
        
        return min(100.0, (completed_actions / total_actions) * 100.0)
    
    def _on_execution_state_change(self, old_state: ProcessState, new_state: ProcessState) -> None:
        """
        Handle execution state changes.
        
        Args:
            old_state: Previous state
            new_state: New state
        """
        try:
            if new_state == ProcessState.RUNNING:
                self.is_executing = True
                
            elif new_state == ProcessState.PAUSED:
                # Execution is still active but paused
                pass
                
            elif new_state == ProcessState.STOPPED:
                self.is_executing = False
                self.pause_event.set()  # Release any waiting threads
        
        except Exception as e:
            logger.error(f"Error handling execution state change: {e}")
    
    def _execute_action(self, action: Dict[str, Any]) -> bool:
        """
        Execute a single action.
        
        Args:
            action: The action to execute
            
        Returns:
            True if action was executed successfully, False otherwise
        """
        action_type = action.get('type')
        
        if not action_type:
            logger.error("Action missing 'type' field")
            return False
        
        handler = self.action_handlers.get(action_type)
        if not handler:
            logger.error(f"No handler for action type: {action_type}")
            return False
        
        try:
            # Apply delay before executing the action
            delay = action.get('delay', 0.0)
            execution_settings = self.settings_manager.get_execution_settings()
            
            # Apply randomness if enabled
            if execution_settings.enable_randomness and delay > 0:
                import random
                randomness_factor = 0.1  # 10% randomness
                delay = delay * (1 + random.uniform(-randomness_factor, randomness_factor))
            
            if delay > 0:
                if self.dry_run:
                    print(f"[DRY RUN] Waiting {delay:.2f} seconds...")
                else:
                    # Wait for delay, but check for pause/stop periodically
                    end_time = time.time() + delay
                    while time.time() < end_time:
                        if not self.state_manager.is_execution_running():
                            return False
                        
                        if self.state_manager.is_execution_paused():
                            # Wait for pause to be cleared
                            self.pause_event.wait(min(0.1, end_time - time.time()))
                            if not self.state_manager.is_execution_running():
                                return False
                        
                        # Small sleep to prevent busy waiting
                        time.sleep(0.01)
            
            # Check for execution state before executing
            if not self.state_manager.is_execution_running():
                return False
            
            # Execute the action
            return handler(action)
            
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return False
    
    def _handle_click(self, action: Dict[str, Any]) -> bool:
        """Handle click action."""
        if self.dry_run:
            print(f"[DRY RUN] Click at ({action.get('abs_x', 0)}, {action.get('abs_y', 0)}) "
                  f"with {action.get('button', 'left')} button")
            return True
        
        try:
            x = action.get('abs_x', 0)
            y = action.get('abs_y', 0)
            button = action.get('button', 'left')
            
            execution_settings = self.settings_manager.get_execution_settings()
            
            # Apply randomness if enabled
            if execution_settings.enable_randomness:
                import random
                radius = execution_settings.randomness_radius
                x += random.randint(-radius, radius)
                y += random.randint(-radius, radius)
            
            # Move mouse to position with optional smoothing
            if execution_settings.enable_smoothing:
                pyautogui.moveTo(x, y, duration=execution_settings.smoothing_duration)
            else:
                pyautogui.moveTo(x, y)
            
            # Perform click
            if button == 'left':
                pyautogui.click()
            elif button == 'right':
                pyautogui.rightClick()
            elif button == 'middle':
                pyautogui.middleClick()
            else:
                pyautogui.click(button=button)
            
            logger.debug(f"Clicked at ({x}, {y}) with {button} button")
            return True
            
        except Exception as e:
            logger.error(f"Error executing click: {e}")
            return False
    
    def _handle_wait(self, action: Dict[str, Any]) -> bool:
        """Handle wait action."""
        seconds = action.get('seconds', 1.0)
        
        if self.dry_run:
            print(f"[DRY RUN] Waiting {seconds:.2f} seconds...")
            return True
        
        try:
            # Wait with pause/stop checking
            end_time = time.time() + seconds
            while time.time() < end_time:
                if not self.state_manager.is_execution_running():
                    return False
                
                if self.state_manager.is_execution_paused():
                    # Wait for pause to be cleared
                    self.pause_event.wait(min(0.1, end_time - time.time()))
                    if not self.state_manager.is_execution_running():
                        return False
                
                # Small sleep to prevent busy waiting
                time.sleep(0.01)
            
            logger.debug(f"Waited {seconds:.2f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Error executing wait: {e}")
            return False
    
    def _handle_keypress(self, action: Dict[str, Any]) -> bool:
        """Handle keypress action."""
        key = action.get('key', '')
        is_combination = action.get('is_combination', False)
        
        if self.dry_run:
            if is_combination:
                print(f"[DRY RUN] Pressing key combination: {key}")
            else:
                print(f"[DRY RUN] Pressing key: {key}")
            return True
        
        try:
            if is_combination:
                # Handle key combinations
                # Split the combination string and press keys in order
                keys = key.split('+')
                
                # Press modifier keys first
                modifier_keys = []
                main_key = None
                
                for k in keys:
                    if k in ['ctrl', 'ctrl_l', 'ctrl_r']:
                        modifier_keys.append('ctrl')
                    elif k in ['alt', 'alt_l', 'alt_r', 'alt_gr']:
                        modifier_keys.append('alt')
                    elif k in ['shift', 'shift_l', 'shift_r']:
                        modifier_keys.append('shift')
                    elif k in ['cmd', 'cmd_l', 'cmd_r', 'win']:
                        modifier_keys.append('win')
                    else:
                        main_key = k
                
                if main_key and modifier_keys:
                    # Use hotkey combination
                    pyautogui.hotkey(*modifier_keys, main_key)
                    logger.debug(f"Pressed key combination: {key}")
                elif main_key:
                    # Just press the main key
                    pyautogui.press(main_key)
                    logger.debug(f"Pressed key: {main_key}")
                else:
                    logger.error(f"Invalid key combination: {key}")
                    return False
            else:
                # Handle single key press
                pyautogui.press(key)
                logger.debug(f"Pressed key: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing keypress: {e}")
            return False
    
    def _handle_scroll(self, action: Dict[str, Any]) -> bool:
        """Handle scroll action."""
        dx = action.get('dx', 0)
        dy = action.get('dy', 0)
        
        if self.dry_run:
            print(f"[DRY RUN] Scrolling: dx={dx}, dy={dy}")
            return True
        
        try:
            if dy != 0:
                pyautogui.scroll(dy)
            if dx != 0:
                pyautogui.hscroll(dx)
            
            logger.debug(f"Scrolled: dx={dx}, dy={dy}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing scroll: {e}")
            return False
    
    def set_dry_run(self, dry_run: bool) -> None:
        """
        Set dry run mode.
        
        Args:
            dry_run: If True, actions are printed but not executed
        """
        self.dry_run = dry_run
        logger.info(f"Dry run mode set to {dry_run}")
    
    def set_callbacks(self,
                     on_action_start: Optional[Callable[[Dict[str, Any]], None]] = None,
                     on_action_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
                     on_execution_start: Optional[Callable[[], None]] = None,
                     on_execution_complete: Optional[Callable[[bool], None]] = None,
                     on_execution_error: Optional[Callable[[Exception], None]] = None,
                     on_loop_start: Optional[Callable[[int], None]] = None,
                     on_loop_complete: Optional[Callable[[int], None]] = None) -> None:
        """
        Set callback functions for various execution events.
        
        Args:
            on_action_start: Called before each action is executed
            on_action_complete: Called after each action is executed
            on_execution_start: Called when execution starts
            on_execution_complete: Called when execution completes
            on_execution_error: Called when an error occurs during execution
            on_loop_start: Called when each loop starts
            on_loop_complete: Called when each loop completes
        """
        self.on_action_start = on_action_start
        self.on_action_complete = on_action_complete
        self.on_execution_start = on_execution_start
        self.on_execution_complete = on_execution_complete
        self.on_execution_error = on_execution_error
        self.on_loop_start = on_loop_start
        self.on_loop_complete = on_loop_complete
    
    def __del__(self):
        """Cleanup when the executor is destroyed."""
        self.stop_execution()