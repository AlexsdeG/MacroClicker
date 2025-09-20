"""
Tests for the recorder module.

This module contains unit tests for the ActionRecorder class.
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

from macroposflow.recorder import ActionRecorder


class TestActionRecorder(unittest.TestCase):
    """Test cases for ActionRecorder class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.recorder = ActionRecorder()
        self.recorded_actions = []
        
        # Mock callback for testing
        def on_action_recorded(action):
            self.recorded_actions.append(action)
        
        self.recorder.on_action_recorded = on_action_recorded
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.recorder.is_active():
            self.recorder.stop_recording()
    
    def test_initialization(self):
        """Test that ActionRecorder initializes correctly."""
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(len(self.recorder.actions), 0)
        self.assertIsNotNone(self.recorder.default_delay)
        self.assertEqual(self.recorder.default_delay, 0.1)
    
    def test_start_recording(self):
        """Test starting recording."""
        self.recorder.start_recording()
        self.assertTrue(self.recorder.is_recording)
        self.assertTrue(self.recorder.is_active())
    
    def test_stop_recording(self):
        """Test stopping recording."""
        self.recorder.start_recording()
        self.assertTrue(self.recorder.is_recording)
        
        actions = self.recorder.stop_recording()
        self.assertFalse(self.recorder.is_recording)
        self.assertFalse(self.recorder.is_active())
        self.assertIsInstance(actions, list)
    
    def test_get_recorded_actions(self):
        """Test getting recorded actions."""
        # Add some test actions
        test_action = {
            "type": "click",
            "monitor": 1,
            "abs_x": 100,
            "abs_y": 200,
            "button": "left",
            "delay": 0.1
        }
        self.recorder.actions.append(test_action)
        
        actions = self.recorder.get_recorded_actions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "click")
        self.assertEqual(actions[0]["abs_x"], 100)
    
    def test_clear_actions(self):
        """Test clearing recorded actions."""
        # Add some test actions
        self.recorder.actions.append({"type": "click", "abs_x": 100, "abs_y": 200})
        self.recorder.actions.append({"type": "wait", "seconds": 1.0})
        
        self.assertEqual(len(self.recorder.actions), 2)
        self.recorder.clear_actions()
        self.assertEqual(len(self.recorder.actions), 0)
    
    def test_set_default_delay(self):
        """Test setting default delay."""
        self.recorder.set_default_delay(0.5)
        self.assertEqual(self.recorder.default_delay, 0.5)
        
        # Test negative delay
        self.recorder.set_default_delay(-0.1)
        self.assertEqual(self.recorder.default_delay, 0.0)
    
    def test_get_action_count(self):
        """Test getting action count."""
        self.assertEqual(self.recorder.get_action_count(), 0)
        
        # Add some actions
        self.recorder.actions.append({"type": "click"})
        self.recorder.actions.append({"type": "wait"})
        
        self.assertEqual(self.recorder.get_action_count(), 2)
    
    def test_is_active(self):
        """Test is_active method."""
        self.assertFalse(self.recorder.is_active())
        
        self.recorder.start_recording()
        self.assertTrue(self.recorder.is_active())
        
        self.recorder.stop_recording()
        self.assertFalse(self.recorder.is_active())
    
    @patch('macroposflow.recorder.mouse.Controller')
    def test_record_mouse_position(self, mock_mouse_controller):
        """Test recording mouse position via F3."""
        # Mock mouse controller
        mock_mouse = Mock()
        mock_mouse.position = (500, 300)
        mock_mouse_controller.return_value = mock_mouse
        
        self.recorder.start_recording()
        
        # Simulate F3 hotkey press
        self.recorder._record_mouse_position()
        
        # Check that action was recorded
        self.assertEqual(len(self.recorded_actions), 1)
        action = self.recorded_actions[0]
        self.assertEqual(action["type"], "click")
        self.assertEqual(action["abs_x"], 500)
        self.assertEqual(action["abs_y"], 300)
        self.assertEqual(action["button"], "left")
        self.assertTrue(action["recorded_via_hotkey"])
        
        self.recorder.stop_recording()
    
    def test_on_mouse_click(self):
        """Test mouse click event handling."""
        self.recorder.start_recording()
        
        # Simulate mouse click
        self.recorder._on_mouse_click(100, 200, Mock(), True)
        
        # Check that action was recorded
        self.assertEqual(len(self.recorded_actions), 1)
        action = self.recorded_actions[0]
        self.assertEqual(action["type"], "click")
        self.assertEqual(action["abs_x"], 100)
        self.assertEqual(action["abs_y"], 200)
        
        self.recorder.stop_recording()
    
    def test_on_mouse_scroll(self):
        """Test mouse scroll event handling."""
        self.recorder.start_recording()
        
        # Simulate mouse scroll
        self.recorder._on_mouse_scroll(100, 200, 0, 1)
        
        # Check that action was recorded
        self.assertEqual(len(self.recorded_actions), 1)
        action = self.recorded_actions[0]
        self.assertEqual(action["type"], "scroll")
        self.assertEqual(action["abs_x"], 100)
        self.assertEqual(action["abs_y"], 200)
        self.assertEqual(action["dx"], 0)
        self.assertEqual(action["dy"], 1)
        
        self.recorder.stop_recording()
    
    def test_on_key_press(self):
        """Test key press event handling."""
        self.recorder.start_recording()
        
        # Mock key object
        mock_key = Mock()
        mock_key.char = 'a'
        
        # Simulate key press
        self.recorder._on_key_press(mock_key)
        
        # Check that action was recorded
        self.assertEqual(len(self.recorded_actions), 1)
        action = self.recorded_actions[0]
        self.assertEqual(action["type"], "keypress")
        self.assertEqual(action["key"], 'a')
        
        self.recorder.stop_recording()
    
    def test_key_to_string(self):
        """Test key to string conversion."""
        # Test KeyCode with char
        mock_key_char = Mock()
        mock_key_char.char = 'a'
        result = self.recorder._key_to_string(mock_key_char)
        self.assertEqual(result, 'a')
        
        # Test Key object
        from pynput.keyboard import Key
        result = self.recorder._key_to_string(Key.space)
        self.assertEqual(result, 'space')
        
        # Test invalid key
        result = self.recorder._key_to_string(None)
        self.assertIsNone(result)
    
    def test_double_start_recording(self):
        """Test starting recording when already recording."""
        self.recorder.start_recording()
        self.assertTrue(self.recorder.is_recording)
        
        # Try to start recording again
        self.recorder.start_recording()
        # Should still be recording, but no error
        self.assertTrue(self.recorder.is_recording)
        
        self.recorder.stop_recording()
    
    def test_stop_recording_when_not_recording(self):
        """Test stopping recording when not recording."""
        self.assertFalse(self.recorder.is_recording)
        
        actions = self.recorder.stop_recording()
        self.assertFalse(self.recorder.is_recording)
        self.assertIsInstance(actions, list)
        self.assertEqual(len(actions), 0)
    
    def test_callback_exception(self):
        """Test handling of callback exceptions."""
        # Set up a callback that raises an exception
        def failing_callback(action):
            raise Exception("Callback failed")
        
        self.recorder.on_action_recorded = failing_callback
        self.recorder.start_recording()
        
        # This should not raise an exception despite the callback failing
        self.recorder._on_mouse_click(100, 200, Mock(), True)
        
        # Action should still be recorded internally
        self.assertEqual(len(self.recorder.actions), 1)
        
        self.recorder.stop_recording()
    
    def test_action_timing(self):
        """Test that action delays are calculated correctly."""
        self.recorder.start_recording()
        
        # Record first action
        self.recorder._on_mouse_click(100, 200, Mock(), True)
        time.sleep(0.1)  # Small delay
        
        # Record second action
        self.recorder._on_mouse_click(200, 300, Mock(), True)
        
        # Check that delays are reasonable
        self.assertEqual(len(self.recorded_actions), 2)
        first_action = self.recorded_actions[0]
        second_action = self.recorded_actions[1]
        
        # First action should have minimal delay
        self.assertGreaterEqual(first_action["delay"], 0.0)
        self.assertLess(first_action["delay"], 0.1)
        
        # Second action should have delay accounting for the sleep
        self.assertGreaterEqual(second_action["delay"], 0.1)
        
        self.recorder.stop_recording()


if __name__ == '__main__':
    unittest.main()