"""
Tests for the executor module.

This module contains unit tests for the ActionExecutor and EmergencyStopHandler classes.
"""

import sys
import os
import time
import threading
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macroposflow.executor import ActionExecutor, EmergencyStopHandler


class TestEmergencyStopHandler(unittest.TestCase):
    """Test cases for EmergencyStopHandler class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.emergency_stop = EmergencyStopHandler()
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.emergency_stop.is_running:
            self.emergency_stop.stop()
    
    def test_initialization(self):
        """Test that EmergencyStopHandler initializes correctly."""
        self.assertFalse(self.emergency_stop.is_running)
        self.assertFalse(self.emergency_stop.is_stopped())
        self.assertIsNotNone(self.emergency_stop.stop_event)
    
    def test_start_stop(self):
        """Test starting and stopping the emergency stop handler."""
        self.assertFalse(self.emergency_stop.is_running)
        
        self.emergency_stop.start()
        self.assertTrue(self.emergency_stop.is_running)
        self.assertFalse(self.emergency_stop.is_stopped())
        
        self.emergency_stop.stop()
        self.assertFalse(self.emergency_stop.is_running)
        self.assertTrue(self.emergency_stop.is_stopped())
    
    def test_double_start(self):
        """Test starting the handler when already running."""
        self.emergency_stop.start()
        self.assertTrue(self.emergency_stop.is_running)
        
        # Try to start again
        self.emergency_stop.start()
        # Should still be running
        self.assertTrue(self.emergency_stop.is_running)
        
        self.emergency_stop.stop()
    
    def test_double_stop(self):
        """Test stopping the handler when not running."""
        self.assertFalse(self.emergency_stop.is_running)
        
        # Should not raise an error
        self.emergency_stop.stop()
        self.assertFalse(self.emergency_stop.is_running)
    
    def test_reset(self):
        """Test resetting the emergency stop event."""
        self.emergency_stop.start()
        self.emergency_stop.stop_event.set()
        self.assertTrue(self.emergency_stop.is_stopped())
        
        self.emergency_stop.reset()
        self.assertFalse(self.emergency_stop.is_stopped())
        
        self.emergency_stop.stop()


class TestActionExecutor(unittest.TestCase):
    """Test cases for ActionExecutor class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.executor = ActionExecutor(dry_run=True)
        self.test_actions = [
            {
                "type": "click",
                "abs_x": 100,
                "abs_y": 200,
                "button": "left",
                "delay": 0.1
            },
            {
                "type": "wait",
                "seconds": 0.5
            },
            {
                "type": "keypress",
                "key": "enter",
                "delay": 0.2
            }
        ]
        
        # Callback tracking
        self.action_start_calls = []
        self.action_complete_calls = []
        self.execution_start_calls = []
        self.execution_complete_calls = []
        self.execution_error_calls = []
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.executor.is_executing_actions():
            self.executor.stop_execution()
    
    def test_initialization(self):
        """Test that ActionExecutor initializes correctly."""
        self.assertFalse(self.executor.is_executing_actions())
        self.assertTrue(self.executor.dry_run)
        self.assertIsNotNone(self.executor.emergency_stop)
        self.assertIn('click', self.executor.action_handlers)
        self.assertIn('wait', self.executor.action_handlers)
        self.assertIn('keypress', self.executor.action_handlers)
    
    def test_set_dry_run(self):
        """Test setting dry run mode."""
        self.assertTrue(self.executor.dry_run)
        
        self.executor.set_dry_run(False)
        self.assertFalse(self.executor.dry_run)
        
        self.executor.set_dry_run(True)
        self.assertTrue(self.executor.dry_run)
    
    def test_execute_actions_empty(self):
        """Test executing empty action list."""
        result = self.executor.execute_actions([])
        self.assertFalse(result)
    
    def test_execute_actions_success(self):
        """Test successful execution of actions."""
        result = self.executor.execute_actions(self.test_actions)
        self.assertTrue(result)
    
    def test_execute_actions_with_emergency_stop(self):
        """Test execution with emergency stop triggered."""
        # Start execution in a separate thread
        self.executor.execute_actions_async(self.test_actions)
        
        # Wait a bit then trigger emergency stop
        time.sleep(0.1)
        self.executor.emergency_stop.stop_event.set()
        
        # Wait for execution to complete
        time.sleep(0.2)
        
        # Should have been stopped
        self.assertFalse(self.executor.is_executing_actions())
    
    def test_execute_actions_async(self):
        """Test asynchronous execution of actions."""
        self.assertFalse(self.executor.is_executing_actions())
        
        self.executor.execute_actions_async(self.test_actions)
        self.assertTrue(self.executor.is_executing_actions())
        
        # Wait for execution to complete
        time.sleep(1.0)
        
        self.assertFalse(self.executor.is_executing_actions())
    
    def test_stop_execution(self):
        """Test stopping execution."""
        self.executor.execute_actions_async(self.test_actions)
        self.assertTrue(self.executor.is_executing_actions())
        
        self.executor.stop_execution()
        self.assertFalse(self.executor.is_executing_actions())
    
    def test_double_execution(self):
        """Test starting execution when already executing."""
        self.executor.execute_actions_async(self.test_actions)
        self.assertTrue(self.executor.is_executing_actions())
        
        # Try to start execution again
        result = self.executor.execute_actions([])
        self.assertFalse(result)  # Should fail
    
    @patch('pyautogui.moveTo')
    @patch('pyautogui.click')
    def test_handle_click(self, mock_click, mock_move_to):
        """Test click action handling."""
        action = {
            "type": "click",
            "abs_x": 100,
            "abs_y": 200,
            "button": "left"
        }
        
        result = self.executor._handle_click(action)
        
        self.assertTrue(result)
        mock_move_to.assert_called_once_with(100, 200, duration=0.1)
        mock_click.assert_called_once()
    
    @patch('pyautogui.rightClick')
    @patch('pyautogui.moveTo')
    def test_handle_click_right_button(self, mock_move_to, mock_right_click):
        """Test click action with right button."""
        action = {
            "type": "click",
            "abs_x": 100,
            "abs_y": 200,
            "button": "right"
        }
        
        result = self.executor._handle_click(action)
        
        self.assertTrue(result)
        mock_move_to.assert_called_once_with(100, 200, duration=0.1)
        mock_right_click.assert_called_once()
    
    @patch('time.sleep')
    def test_handle_wait(self, mock_sleep):
        """Test wait action handling."""
        action = {
            "type": "wait",
            "seconds": 1.5
        }
        
        result = self.executor._handle_wait(action)
        
        self.assertTrue(result)
        mock_sleep.assert_called_once_with(1.5)
    
    @patch('pyautogui.press')
    def test_handle_keypress(self, mock_press):
        """Test keypress action handling."""
        action = {
            "type": "keypress",
            "key": "enter"
        }
        
        result = self.executor._handle_keypress(action)
        
        self.assertTrue(result)
        mock_press.assert_called_once_with("enter")
    
    @patch('pyautogui.scroll')
    def test_handle_scroll_vertical(self, mock_scroll):
        """Test scroll action handling (vertical)."""
        action = {
            "type": "scroll",
            "dy": 1
        }
        
        result = self.executor._handle_scroll(action)
        
        self.assertTrue(result)
        mock_scroll.assert_called_once_with(1)
    
    @patch('pyautogui.hscroll')
    def test_handle_scroll_horizontal(self, mock_hscroll):
        """Test scroll action handling (horizontal)."""
        action = {
            "type": "scroll",
            "dx": 1
        }
        
        result = self.executor._handle_scroll(action)
        
        self.assertTrue(result)
        mock_hscroll.assert_called_once_with(1)
    
    def test_handle_invalid_action_type(self):
        """Test handling invalid action type."""
        action = {
            "type": "invalid_type"
        }
        
        result = self.executor._execute_action(action)
        self.assertFalse(result)
    
    def test_handle_action_missing_type(self):
        """Test handling action missing type."""
        action = {
            "abs_x": 100,
            "abs_y": 200
        }
        
        result = self.executor._execute_action(action)
        self.assertFalse(result)
    
    def test_callbacks(self):
        """Test that callbacks are called correctly."""
        # Set up callbacks
        def on_action_start(action):
            self.action_start_calls.append(action)
        
        def on_action_complete(action):
            self.action_complete_calls.append(action)
        
        def on_execution_start():
            self.execution_start_calls.append(True)
        
        def on_execution_complete(success):
            self.execution_complete_calls.append(success)
        
        self.executor.set_callbacks(
            on_action_start=on_action_start,
            on_action_complete=on_action_complete,
            on_execution_start=on_execution_start,
            on_execution_complete=on_execution_complete
        )
        
        # Execute actions
        result = self.executor.execute_actions(self.test_actions)
        
        # Check callbacks were called
        self.assertEqual(len(self.execution_start_calls), 1)
        self.assertEqual(len(self.execution_complete_calls), 1)
        self.assertEqual(len(self.action_start_calls), len(self.test_actions))
        self.assertEqual(len(self.action_complete_calls), len(self.test_actions))
        self.assertTrue(self.execution_complete_calls[0])
    
    def test_error_callback(self):
        """Test error callback handling."""
        def on_execution_error(error):
            self.execution_error_calls.append(error)
        
        self.executor.set_callbacks(on_execution_error=on_execution_error)
        
        # Create an action that will cause an error
        bad_action = {
            "type": "click",
            "abs_x": "invalid",  # This should cause an error
            "abs_y": 200
        }
        
        result = self.executor.execute_actions([bad_action])
        
        # Check that error callback was called
        self.assertEqual(len(self.execution_error_calls), 1)
        self.assertIsInstance(self.execution_error_calls[0], Exception)
        self.assertFalse(result)
    
    def test_action_delay(self):
        """Test that action delays are applied correctly."""
        with patch('time.sleep') as mock_sleep:
            action = {
                "type": "click",
                "abs_x": 100,
                "abs_y": 200,
                "button": "left",
                "delay": 0.5
            }
            
            result = self.executor._execute_action(action)
            
            self.assertTrue(result)
            mock_sleep.assert_called_once_with(0.5)
    
    def test_emergency_stop_during_action(self):
        """Test emergency stop during action execution."""
        # Set up emergency stop to trigger during execution
        def trigger_stop():
            time.sleep(0.1)
            self.executor.emergency_stop.stop_event.set()
        
        # Start stop trigger thread
        stop_thread = threading.Thread(target=trigger_stop)
        stop_thread.start()
        
        # Execute long-running action
        long_action = [
            {
                "type": "wait",
                "seconds": 1.0
            }
        ]
        
        result = self.executor.execute_actions(long_action)
        
        # Should have been stopped
        self.assertFalse(result)
        
        # Clean up
        stop_thread.join()


if __name__ == '__main__':
    unittest.main()