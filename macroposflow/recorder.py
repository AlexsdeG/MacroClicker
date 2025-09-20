"""
Recorder module for MacroPosFlow.

This module provides functionality to record mouse and keyboard actions
using configurable hotkeys and stores them as action sequences with proper state management.
"""

import threading
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Set, Tuple
from pynput import mouse, keyboard
from pynput.keyboard import KeyCode, Key

from .settings import SettingsManager, KeyBindings
from .state_manager import StateManager, ProcessState

logger = logging.getLogger(__name__)


class GlobalKeyHandler:
    """
    Global key handler for special hotkeys.
    
    This class handles global hotkeys that should not be recorded
    and are used for controlling recording and execution states.
    """
    
    def __init__(self, settings_manager: SettingsManager, state_manager: StateManager):
        """
        Initialize the GlobalKeyHandler.
        
        Args:
            settings_manager: Settings manager for key bindings
            state_manager: State manager for state changes
        """
        self.settings_manager = settings_manager
        self.state_manager = state_manager
        
        # Listeners
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        
        # Key tracking for combination detection
        self.pressed_keys: Set[keyboard.Key] = set()
        self.modifier_keys = {
            Key.ctrl, Key.ctrl_l, Key.ctrl_r,
            Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr,
            Key.shift, Key.shift_l, Key.shift_r,
            Key.cmd, Key.cmd_l, Key.cmd_r
        }
        
        # Callbacks
        self.on_record_position: Optional[Callable[[], None]] = None
        self.on_record_alt_click: Optional[Callable[[int, int], None]] = None
        
        logger.info("GlobalKeyHandler initialized")
    
    def start_listeners(self) -> None:
        """Start global key and mouse listeners."""
        if self.keyboard_listener and self.keyboard_listener.is_alive():
            return
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Start mouse listener for alternative click recording
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()
        
        logger.info("Global key listeners started")
    
    def stop_listeners(self) -> None:
        """Stop global key and mouse listeners."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        logger.info("Global key listeners stopped")
    
    def _on_key_press(self, key) -> bool:
        """
        Handle global key press events.
        
        Args:
            key: The pressed key
            
        Returns:
            False to stop the listener, True to continue
        """
        try:
            # Add key to pressed keys set
            self.pressed_keys.add(key)
            
            # Get current key bindings
            key_bindings = self.settings_manager.get_key_bindings()
            
            # Check for key combinations
            active_modifiers = self.pressed_keys.intersection(self.modifier_keys)
            
            # Check recording control keys
            if self._check_key_combination(active_modifiers, key, key_bindings.record_start_stop):
                # Toggle recording state
                if self.state_manager.is_recording_running():
                    self.state_manager.pause_recording("Hotkey pressed")
                elif self.state_manager.is_recording_paused():
                    self.state_manager.resume_recording("Hotkey pressed")
                else:
                    self.state_manager.start_recording("Hotkey pressed")
                return True  # Don't record this key
            
            elif self._check_key_combination(active_modifiers, key, key_bindings.record_pause_resume):
                # Toggle pause state
                if self.state_manager.is_recording_running():
                    self.state_manager.pause_recording("Hotkey pressed")
                elif self.state_manager.is_recording_paused():
                    self.state_manager.resume_recording("Hotkey pressed")
                return True  # Don't record this key
            
            elif self._check_key_combination(active_modifiers, key, key_bindings.record_position):
                # Record current mouse position
                if self.state_manager.is_recording_running() and self.on_record_position:
                    self.on_record_position()
                return True  # Don't record this key
            
            # Check execution control keys
            elif self._check_key_combination(active_modifiers, key, key_bindings.execute_start_stop):
                # Toggle execution state
                if self.state_manager.is_execution_running():
                    self.state_manager.pause_execution("Hotkey pressed")
                elif self.state_manager.is_execution_paused():
                    self.state_manager.resume_execution("Hotkey pressed")
                else:
                    self.state_manager.start_execution("Hotkey pressed")
                return True  # Don't record this key
            
            elif self._check_key_combination(active_modifiers, key, key_bindings.execute_pause_resume):
                # Toggle execution pause state
                if self.state_manager.is_execution_running():
                    self.state_manager.pause_execution("Hotkey pressed")
                elif self.state_manager.is_execution_paused():
                    self.state_manager.resume_execution("Hotkey pressed")
                return True  # Don't record this key
            
            elif self._check_key_combination(active_modifiers, key, key_bindings.execute_kill):
                # Emergency stop execution
                self.state_manager.stop_execution("Emergency kill hotkey")
                return True  # Don't record this key
            
            # Check global emergency stop
            elif self._check_key_combination(active_modifiers, key, key_bindings.global_emergency_stop):
                # Global emergency stop - stop both recording and execution
                if self.state_manager.is_recording_active():
                    self.state_manager.stop_recording("Global emergency stop")
                if self.state_manager.is_execution_active():
                    self.state_manager.stop_execution("Global emergency stop")
                return False  # Stop the listener
            
        except Exception as e:
            logger.error(f"Error in global key handler: {e}")
        
        return True  # Continue listening
    
    def _on_key_release(self, key) -> None:
        """
        Handle global key release events.
        
        Args:
            key: The released key
        """
        # Remove key from pressed keys set
        self.pressed_keys.discard(key)
    
    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """
        Handle global mouse click events for alternative click recording.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            pressed: Whether the button was pressed or released
        """
        if not pressed:
            return
        
        try:
            # Check if this is an alternative click recording combination
            key_bindings = self.settings_manager.get_key_bindings()
            active_modifiers = self.pressed_keys.intersection(self.modifier_keys)
            
            # Check for right click with ctrl modifier
            if (button == mouse.Button.right and 
                self._check_key_combination(active_modifiers, None, key_bindings.record_alt_click)):
                
                if self.state_manager.is_recording_running() and self.on_record_alt_click:
                    self.on_record_alt_click(x, y)
        
        except Exception as e:
            logger.error(f"Error in global mouse handler: {e}")
    
    def _check_key_combination(self, active_modifiers: Set[keyboard.Key], 
                              main_key: Optional[keyboard.Key], 
                              target_combination: List[str]) -> bool:
        """
        Check if the current key combination matches the target combination.
        
        Args:
            active_modifiers: Set of currently pressed modifier keys
            main_key: The main key that was pressed (optional)
            target_combination: List of strings representing the target combination
            
        Returns:
            True if combination matches, False otherwise
        """
        if not target_combination:
            return False
        
        # Convert target combination to normalized form
        target_modifiers = set()
        target_main_key = None
        
        for key_str in target_combination:
            if key_str == 'ctrl':
                target_modifiers.update([Key.ctrl, Key.ctrl_l, Key.ctrl_r])
            elif key_str == 'alt':
                target_modifiers.update([Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr])
            elif key_str == 'shift':
                target_modifiers.update([Key.shift, Key.shift_l, Key.shift_r])
            elif key_str == 'cmd' or key_str == 'win':
                target_modifiers.update([Key.cmd, Key.cmd_l, Key.cmd_r])
            else:
                # This is the main key
                target_main_key = key_str
        
        # Check if modifiers match
        if target_modifiers:
            if not active_modifiers.intersection(target_modifiers):
                return False
            # Check if there are extra modifiers
            extra_modifiers = active_modifiers - target_modifiers
            if extra_modifiers:
                return False
        
        # Check if main key matches
        if target_main_key:
            if main_key is None:
                return False
            
            # Convert main_key to string for comparison
            main_key_str = self._key_to_string(main_key)
            if main_key_str != target_main_key:
                return False
        
        return True
    
    def _key_to_string(self, key) -> Optional[str]:
        """
        Convert a key object to a string representation.
        
        Args:
            key: The key object
            
        Returns:
            String representation of the key, or None if conversion fails
        """
        try:
            if isinstance(key, KeyCode):
                return key.char.lower() if key.char else None
            elif isinstance(key, Key):
                key_str = str(key).replace('Key.', '')
                
                # Normalize modifier keys
                modifier_mapping = {
                    'ctrl_l': 'ctrl',
                    'ctrl_r': 'ctrl',
                    'alt_l': 'alt',
                    'alt_r': 'alt',
                    'alt_gr': 'alt',
                    'shift_l': 'shift',
                    'shift_r': 'shift',
                    'cmd_l': 'cmd',
                    'cmd_r': 'cmd',
                    'cmd': 'win',
                }
                
                return modifier_mapping.get(key_str, key_str)
            else:
                return str(key)
        except Exception as e:
            logger.error(f"Error converting key to string: {e}")
            return None
    
    def set_record_position_callback(self, callback: Optional[Callable[[], None]]) -> None:
        """
        Set callback for recording position.
        
        Args:
            callback: Function to call when position recording is triggered
        """
        self.on_record_position = callback
    
    def set_record_alt_click_callback(self, callback: Optional[Callable[[int, int], None]]) -> None:
        """
        Set callback for alternative click recording.
        
        Args:
            callback: Function to call when alternative click recording is triggered
        """
        self.on_record_alt_click = callback


class ActionRecorder:
    """
    Records mouse and keyboard actions using configurable hotkeys.
    
    This class provides functionality to record mouse clicks and keyboard inputs
    using configurable hotkeys and stores them as structured actions with proper state management.
    """
    
    def __init__(self, 
                 settings_manager: Optional[SettingsManager] = None,
                 state_manager: Optional[StateManager] = None,
                 on_action_recorded: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize the ActionRecorder.
        
        Args:
            settings_manager: Settings manager for configuration
            state_manager: State manager for state management
            on_action_recorded: Callback function called when an action is recorded
        """
        self.settings_manager = settings_manager or SettingsManager()
        self.state_manager = state_manager or StateManager()
        
        # Actions and timing
        self.actions: List[Dict[str, Any]] = []
        self.recording_start_time = 0.0
        self.last_action_time = 0.0
        self.pause_start_time = 0.0
        
        # Threading locks
        self.recording_lock = threading.Lock()
        
        # Listeners
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        
        # Global key handler
        self.global_key_handler = GlobalKeyHandler(self.settings_manager, self.state_manager)
        self.global_key_handler.set_record_position_callback(self._record_mouse_position)
        self.global_key_handler.set_record_alt_click_callback(self._record_alt_click)
        
        # Callbacks
        self.on_action_recorded = on_action_recorded
        
        # Key tracking for combination detection
        self.pressed_keys: Set[keyboard.Key] = set()
        self.modifier_keys = {
            Key.ctrl, Key.ctrl_l, Key.ctrl_r,
            Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr,
            Key.shift, Key.shift_l, Key.shift_r,
            Key.cmd, Key.cmd_l, Key.cmd_r
        }
        
        # Set up state change callbacks
        self.state_manager.add_recording_state_callback(self._on_recording_state_change)
        
        logger.info("ActionRecorder initialized")
    
    def start_recording(self) -> None:
        """
        Start recording actions.
        
        This method prepares the recorder for recording but doesn't start immediately.
        The actual recording starts when the user presses the start hotkey.
        """
        with self.recording_lock:
            if self.state_manager.is_recording_active():
                logger.warning("Recording already in progress")
                return
            
            # Clear actions and reset timing
            self.actions.clear()
            self.recording_start_time = 0.0
            self.last_action_time = 0.0
            self.pause_start_time = 0.0
            
            # Start global key listeners
            self.global_key_handler.start_listeners()
            
            logger.info("Recording system initialized - waiting for start hotkey")
    
    def stop_recording(self) -> List[Dict[str, Any]]:
        """
        Stop recording and return recorded actions.
        
        Returns:
            List of recorded actions
        """
        with self.recording_lock:
            if not self.state_manager.is_recording_active():
                logger.warning("No recording in progress")
                return self.actions.copy()
            
            # Stop state management
            self.state_manager.stop_recording("User request")
            
            # Stop listeners
            self._stop_listeners()
            
            logger.info(f"Recording stopped. Total actions: {len(self.actions)}")
            return self.actions.copy()
    
    def pause_recording(self) -> None:
        """Pause recording."""
        with self.recording_lock:
            if not self.state_manager.is_recording_running():
                logger.warning("Cannot pause - recording is not running")
                return
            
            self.pause_start_time = time.time()
            self.state_manager.pause_recording("User request")
            logger.info("Recording paused")
    
    def resume_recording(self) -> None:
        """Resume recording from paused state."""
        with self.recording_lock:
            if not self.state_manager.is_recording_paused():
                logger.warning("Cannot resume - recording is not paused")
                return
            
            # Adjust timing to account for pause duration
            if self.pause_start_time > 0:
                pause_duration = time.time() - self.pause_start_time
                self.last_action_time += pause_duration
                self.pause_start_time = 0.0
            
            self.state_manager.resume_recording("User request")
            logger.info("Recording resumed")
    
    def get_recorded_actions(self) -> List[Dict[str, Any]]:
        """
        Get a copy of the recorded actions.
        
        Returns:
            List of recorded actions
        """
        with self.recording_lock:
            return self.actions.copy()
    
    def clear_actions(self) -> None:
        """Clear all recorded actions."""
        with self.recording_lock:
            self.actions.clear()
            logger.info("Cleared all recorded actions")
    
    def _start_listeners(self) -> None:
        """Start action recording listeners."""
        if self.mouse_listener and self.mouse_listener.is_alive():
            return
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        logger.info("Action recording listeners started")
    
    def _stop_listeners(self) -> None:
        """Stop all listeners."""
        # Stop global key handler
        self.global_key_handler.stop_listeners()
        
        # Stop action recording listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        logger.info("All listeners stopped")
    
    def _on_recording_state_change(self, old_state: ProcessState, new_state: ProcessState) -> None:
        """
        Handle recording state changes.
        
        Args:
            old_state: Previous state
            new_state: New state
        """
        try:
            if new_state == ProcessState.RUNNING:
                # Start recording actions
                self.recording_start_time = time.time()
                self.last_action_time = self.recording_start_time
                self._start_listeners()
                logger.info("Action recording started")
                
            elif new_state == ProcessState.PAUSED:
                # Pause recording actions
                self._stop_listeners()
                logger.info("Action recording paused")
                
            elif new_state == ProcessState.STOPPED:
                # Stop recording actions
                self._stop_listeners()
                
                # Update recording info
                self.state_manager.update_recording_info(
                    action_count=len(self.actions)
                )
                logger.info("Action recording stopped")
        
        except Exception as e:
            logger.error(f"Error handling recording state change: {e}")
    
    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """
        Handle mouse click events.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            pressed: Whether the button was pressed or released
        """
        if not self.state_manager.is_recording_running() or not pressed:
            return
        
        # Skip if this is a global hotkey combination
        key_bindings = self.settings_manager.get_key_bindings()
        active_modifiers = self.pressed_keys.intersection(self.modifier_keys)
        
        if (button == mouse.Button.right and 
            self.global_key_handler._check_key_combination(
                active_modifiers, None, key_bindings.record_alt_click)):
            return  # This is handled by the global handler
        
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        # For Phase 1, we assume single monitor (monitor 1)
        # In Phase 3, this will be updated with multi-monitor support
        action = {
            "type": "click",
            "monitor": 1,
            "rel_x": 0.5,  # Placeholder - will be calculated properly in Phase 3
            "rel_y": 0.5,  # Placeholder - will be calculated properly in Phase 3
            "abs_x": x,
            "abs_y": y,
            "button": str(button).split('.')[-1].lower(),
            "delay": max(0.0, delay),
            "timestamp": current_time
        }
        
        self._add_action(action)
    
    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """
        Handle mouse scroll events.
        
        Args:
            x: X coordinate
            y: Y coordinate
            dx: Horizontal scroll
            dy: Vertical scroll
        """
        if not self.state_manager.is_recording_running():
            return
        
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        action = {
            "type": "scroll",
            "monitor": 1,
            "rel_x": 0.5,  # Placeholder
            "rel_y": 0.5,  # Placeholder
            "abs_x": x,
            "abs_y": y,
            "dx": dx,
            "dy": dy,
            "delay": max(0.0, delay),
            "timestamp": current_time
        }
        
        self._add_action(action)
    
    def _on_key_press(self, key) -> None:
        """
        Handle key press events.
        
        Args:
            key: The pressed key
        """
        if not self.state_manager.is_recording_running():
            return
        
        # Skip global hotkeys - they are handled by the global key handler
        key_bindings = self.settings_manager.get_key_bindings()
        active_modifiers = self.pressed_keys.intersection(self.modifier_keys)
        
        # Check if this is any global hotkey
        global_hotkeys = [
            key_bindings.record_start_stop,
            key_bindings.record_pause_resume,
            key_bindings.record_position,
            key_bindings.execute_start_stop,
            key_bindings.execute_pause_resume,
            key_bindings.execute_kill,
            key_bindings.global_emergency_stop
        ]
        
        for hotkey in global_hotkeys:
            if self.global_key_handler._check_key_combination(active_modifiers, key, hotkey):
                return  # This is a global hotkey, don't record it
        
        # Add key to pressed keys set
        self.pressed_keys.add(key)
        
        # If this is a modifier key, don't record it yet - wait for the combination
        if key in self.modifier_keys:
            return
        
        # Check if this is part of a key combination
        active_modifiers = self.pressed_keys.intersection(self.modifier_keys)
        
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        if active_modifiers:
            # This is a key combination
            modifier_strs = [self.global_key_handler._key_to_string(mod) for mod in active_modifiers]
            main_key_str = self.global_key_handler._key_to_string(key)
            
            if main_key_str:
                # Create combination key string
                combination_str = '+'.join(sorted(modifier_strs) + [main_key_str])
                
                action = {
                    "type": "keypress",
                    "key": combination_str,
                    "delay": max(0.0, delay),
                    "timestamp": current_time,
                    "is_combination": True,
                    "modifiers": [self.global_key_handler._key_to_string(mod) for mod in active_modifiers],
                    "main_key": main_key_str
                }
                
                self._add_action(action)
        else:
            # This is a single key press
            key_str = self.global_key_handler._key_to_string(key)
            if key_str:
                action = {
                    "type": "keypress",
                    "key": key_str,
                    "delay": max(0.0, delay),
                    "timestamp": current_time,
                    "is_combination": False
                }
                
                self._add_action(action)
    
    def _on_key_release(self, key) -> None:
        """
        Handle key release events.
        
        Args:
            key: The released key
        """
        # Remove key from pressed keys set
        self.pressed_keys.discard(key)
        
        # For Phase 1, we only record key presses, not releases
        pass
    
    def _record_mouse_position(self) -> None:
        """Record current mouse position when position hotkey is pressed."""
        if not self.state_manager.is_recording_running():
            return
        
        try:
            # Get current mouse position
            current_mouse = mouse.Controller()
            x, y = current_mouse.position
            
            current_time = time.time()
            delay = current_time - self.last_action_time
            self.last_action_time = current_time
            
            action = {
                "type": "click",
                "monitor": 1,
                "rel_x": 0.5,  # Placeholder - will be calculated properly in Phase 3
                "rel_y": 0.5,  # Placeholder - will be calculated properly in Phase 3
                "abs_x": x,
                "abs_y": y,
                "button": "left",
                "delay": max(0.0, delay),
                "timestamp": current_time,
                "recorded_via_hotkey": True
            }
            
            self._add_action(action)
            logger.info(f"Recorded mouse position via hotkey: ({x}, {y})")
            
        except Exception as e:
            logger.error(f"Error recording mouse position: {e}")
    
    def _record_alt_click(self, x: int, y: int) -> None:
        """Record alternative click at position."""
        if not self.state_manager.is_recording_running():
            return
        
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        action = {
            "type": "click",
            "monitor": 1,
            "rel_x": 0.5,  # Placeholder
            "rel_y": 0.5,  # Placeholder
            "abs_x": x,
            "abs_y": y,
            "button": "left",
            "delay": max(0.0, delay),
            "timestamp": current_time,
            "recorded_via_alt_hotkey": True
        }
        
        self._add_action(action)
        logger.info(f"Recorded alternative click at: ({x}, {y})")
    
    def _add_action(self, action: Dict[str, Any]) -> None:
        """
        Add an action to the recorded actions list.
        
        Args:
            action: The action to add
        """
        with self.recording_lock:
            self.actions.append(action)
            logger.debug(f"Recorded action: {action}")
            
            # Update recording info
            self.state_manager.update_recording_info(
                action_count=len(self.actions)
            )
            
            # Call callback if provided
            if self.on_action_recorded:
                try:
                    self.on_action_recorded(action)
                except Exception as e:
                    logger.error(f"Error in action recorded callback: {e}")
    
    def get_action_count(self) -> int:
        """
        Get the number of recorded actions.
        
        Returns:
            Number of recorded actions
        """
        with self.recording_lock:
            return len(self.actions)
    
    def is_recording(self) -> bool:
        """
        Check if recording is currently active.
        
        Returns:
            True if recording is active, False otherwise
        """
        return self.state_manager.is_recording_active()
    
    def __del__(self):
        """Cleanup when the recorder is destroyed."""
        self.stop_recording()