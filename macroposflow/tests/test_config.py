"""
Tests for the config module.

This module contains unit tests for the ConfigManager class.
"""

import sys
import os
import json
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macroposflow.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        
        # Test data
        self.test_actions = [
            {
                "type": "click",
                "monitor": 1,
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
        
        self.test_metadata = {
            "name": "test_macro",
            "description": "Test macro for unit testing",
            "author": "Test Suite",
            "version": "1.0"
        }
    
    def tearDown(self):
        """Clean up after each test method."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test that ConfigManager initializes correctly."""
        self.assertIsNotNone(self.config_manager.config_dir)
        self.assertTrue(self.config_manager.config_dir.exists())
        self.assertIsInstance(self.config_manager.global_settings, dict)
        self.assertIn('default_delay', self.config_manager.global_settings)
    
    def test_initialization_with_default_dir(self):
        """Test ConfigManager initialization with default directory."""
        config_manager = ConfigManager()
        self.assertIsNotNone(config_manager.config_dir)
        self.assertTrue(config_manager.config_dir.exists())
    
    def test_save_macro_success(self):
        """Test successful macro saving."""
        result = self.config_manager.save_macro(
            self.test_actions,
            "test_macro",
            self.test_metadata
        )
        
        self.assertTrue(result)
        
        # Check that file was created
        macro_file = self.config_manager.config_dir / "test_macro.json"
        self.assertTrue(macro_file.exists())
        
        # Check file contents
        with open(macro_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('meta', data)
        self.assertIn('actions', data)
        self.assertEqual(len(data['actions']), len(self.test_actions))
        self.assertEqual(data['meta']['name'], 'test_macro')
    
    def test_save_macro_without_extension(self):
        """Test saving macro without .json extension."""
        result = self.config_manager.save_macro(
            self.test_actions,
            "test_macro",  # No .json extension
            self.test_metadata
        )
        
        self.assertTrue(result)
        
        # Check that file was created with .json extension
        macro_file = self.config_manager.config_dir / "test_macro.json"
        self.assertTrue(macro_file.exists())
    
    def test_save_macro_without_metadata(self):
        """Test saving macro without metadata."""
        result = self.config_manager.save_macro(
            self.test_actions,
            "test_macro"
        )
        
        self.assertTrue(result)
        
        # Check that default metadata was added
        macro_file = self.config_manager.config_dir / "test_macro.json"
        with open(macro_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('meta', data)
        self.assertIn('name', data['meta'])
        self.assertIn('created', data['meta'])
        self.assertIn('author', data['meta'])
    
    def test_save_macro_invalid_actions(self):
        """Test saving macro with invalid actions."""
        invalid_actions = [
            {
                "type": "invalid_type",
                "abs_x": 100,
                "abs_y": 200
            }
        ]
        
        result = self.config_manager.save_macro(
            invalid_actions,
            "invalid_macro"
        )
        
        self.assertFalse(result)
        
        # File should not have been created
        macro_file = self.config_manager.config_dir / "invalid_macro.json"
        self.assertFalse(macro_file.exists())
    
    def test_load_macro_success(self):
        """Test successful macro loading."""
        # First save a macro
        self.config_manager.save_macro(
            self.test_actions,
            "test_macro",
            self.test_metadata
        )
        
        # Then load it
        config = self.config_manager.load_macro("test_macro")
        
        self.assertIsNotNone(config)
        self.assertIn('meta', config)
        self.assertIn('actions', config)
        self.assertEqual(len(config['actions']), len(self.test_actions))
        self.assertEqual(config['meta']['name'], 'test_macro')
    
    def test_load_macro_without_extension(self):
        """Test loading macro without .json extension."""
        # First save a macro
        self.config_manager.save_macro(
            self.test_actions,
            "test_macro",
            self.test_metadata
        )
        
        # Load without extension
        config = self.config_manager.load_macro("test_macro")
        
        self.assertIsNotNone(config)
        self.assertEqual(config['meta']['name'], 'test_macro')
    
    def test_load_macro_nonexistent(self):
        """Test loading non-existent macro."""
        config = self.config_manager.load_macro("nonexistent_macro")
        self.assertIsNone(config)
    
    def test_load_macro_invalid_json(self):
        """Test loading macro with invalid JSON."""
        # Create invalid JSON file
        macro_file = self.config_manager.config_dir / "invalid.json"
        with open(macro_file, 'w') as f:
            f.write("invalid json content")
        
        config = self.config_manager.load_macro("invalid")
        self.assertIsNone(config)
    
    def test_load_macro_invalid_structure(self):
        """Test loading macro with invalid structure."""
        # Create macro file with invalid structure
        macro_file = self.config_manager.config_dir / "invalid_structure.json"
        with open(macro_file, 'w') as f:
            json.dump({
                "invalid_structure": True
            }, f)
        
        config = self.config_manager.load_macro("invalid_structure")
        self.assertIsNone(config)
    
    def test_list_macros_empty(self):
        """Test listing macros when none exist."""
        macros = self.config_manager.list_macros()
        self.assertEqual(len(macros), 0)
    
    def test_list_macros_with_files(self):
        """Test listing macros when files exist."""
        # Save some macros
        self.config_manager.save_macro(self.test_actions, "macro1")
        self.config_manager.save_macro(self.test_actions, "macro2")
        
        macros = self.config_manager.list_macros()
        self.assertEqual(len(macros), 2)
        self.assertIn("macro1", macros)
        self.assertIn("macro2", macros)
    
    def test_delete_macro_success(self):
        """Test successful macro deletion."""
        # Save a macro first
        self.config_manager.save_macro(self.test_actions, "test_macro")
        
        # Check that file exists
        macro_file = self.config_manager.config_dir / "test_macro.json"
        self.assertTrue(macro_file.exists())
        
        # Delete it
        result = self.config_manager.delete_macro("test_macro")
        self.assertTrue(result)
        
        # Check that file is gone
        self.assertFalse(macro_file.exists())
    
    def test_delete_macro_nonexistent(self):
        """Test deleting non-existent macro."""
        result = self.config_manager.delete_macro("nonexistent_macro")
        self.assertFalse(result)
    
    def test_delete_macro_without_extension(self):
        """Test deleting macro without .json extension."""
        # Save a macro first
        self.config_manager.save_macro(self.test_actions, "test_macro")
        
        # Delete without extension
        result = self.config_manager.delete_macro("test_macro")
        self.assertTrue(result)
        
        # Check that file is gone
        macro_file = self.config_manager.config_dir / "test_macro.json"
        self.assertFalse(macro_file.exists())
    
    def test_get_macro_info_success(self):
        """Test getting macro info successfully."""
        # Save a macro first
        self.config_manager.save_macro(
            self.test_actions,
            "test_macro",
            self.test_metadata
        )
        
        info = self.config_manager.get_macro_info("test_macro")
        
        self.assertIsNotNone(info)
        self.assertEqual(info['name'], 'test_macro')
        self.assertEqual(info['description'], 'Test macro for unit testing')
        self.assertEqual(info['action_count'], len(self.test_actions))
        self.assertIn('file_size', info)
        self.assertIn('created', info)
        self.assertIn('file_modified', info)
    
    def test_get_macro_info_nonexistent(self):
        """Test getting info for non-existent macro."""
        info = self.config_manager.get_macro_info("nonexistent_macro")
        self.assertIsNone(info)
    
    def test_save_global_settings(self):
        """Test saving global settings."""
        # Modify some settings
        self.config_manager.set_global_setting('default_delay', 0.5)
        self.config_manager.set_global_setting('mouse_speed', 2.0)
        
        result = self.config_manager.save_global_settings()
        self.assertTrue(result)
        
        # Check that settings file was created
        settings_file = self.config_manager.config_dir / "settings.json"
        self.assertTrue(settings_file.exists())
        
        # Check file contents
        with open(settings_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('global_settings', data)
        self.assertIn('last_updated', data)
        self.assertEqual(data['global_settings']['default_delay'], 0.5)
        self.assertEqual(data['global_settings']['mouse_speed'], 2.0)
    
    def test_load_global_settings(self):
        """Test loading global settings."""
        # Save some settings first
        settings = {
            'default_delay': 0.3,
            'mouse_speed': 1.5,
            'custom_setting': 'test_value'
        }
        
        settings_file = self.config_manager.config_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump({
                'global_settings': settings,
                'last_updated': '2023-01-01T00:00:00'
            }, f)
        
        # Create new ConfigManager to test loading
        new_config_manager = ConfigManager(self.temp_dir)
        
        self.assertEqual(new_config_manager.get_global_setting('default_delay'), 0.3)
        self.assertEqual(new_config_manager.get_global_setting('mouse_speed'), 1.5)
        self.assertEqual(new_config_manager.get_global_setting('custom_setting'), 'test_value')
    
    def test_get_global_setting(self):
        """Test getting global setting values."""
        # Test existing setting
        delay = self.config_manager.get_global_setting('default_delay')
        self.assertIsNotNone(delay)
        
        # Test non-existing setting with default
        custom = self.config_manager.get_global_setting('nonexistent', 'default_value')
        self.assertEqual(custom, 'default_value')
        
        # Test non-existing setting without default
        custom = self.config_manager.get_global_setting('nonexistent')
        self.assertIsNone(custom)
    
    def test_set_global_setting(self):
        """Test setting global setting values."""
        # Set a new setting
        self.config_manager.set_global_setting('test_setting', 'test_value')
        
        # Check that it was set
        value = self.config_manager.get_global_setting('test_setting')
        self.assertEqual(value, 'test_value')
        
        # Update existing setting
        self.config_manager.set_global_setting('test_setting', 'new_value')
        value = self.config_manager.get_global_setting('test_setting')
        self.assertEqual(value, 'new_value')
    
    def test_get_global_settings(self):
        """Test getting all global settings."""
        settings = self.config_manager.get_global_settings()
        
        self.assertIsInstance(settings, dict)
        self.assertIn('default_delay', settings)
        self.assertIn('emergency_stop_key', settings)
        self.assertIn('record_hotkey', settings)
    
    def test_update_global_settings(self):
        """Test updating multiple global settings."""
        new_settings = {
            'default_delay': 0.7,
            'mouse_speed': 1.8,
            'new_setting': 'new_value'
        }
        
        self.config_manager.update_global_settings(new_settings)
        
        self.assertEqual(self.config_manager.get_global_setting('default_delay'), 0.7)
        self.assertEqual(self.config_manager.get_global_setting('mouse_speed'), 1.8)
        self.assertEqual(self.config_manager.get_global_setting('new_setting'), 'new_value')
        
        # Check that existing settings not in update are preserved
        self.assertIsNotNone(self.config_manager.get_global_setting('emergency_stop_key'))
    
    def test_validate_actions_valid(self):
        """Test validation of valid actions."""
        valid_actions = [
            {
                "type": "click",
                "monitor": 1,
                "abs_x": 100,
                "abs_y": 200,
                "button": "left"
            },
            {
                "type": "wait",
                "seconds": 1.0
            },
            {
                "type": "keypress",
                "key": "enter"
            },
            {
                "type": "scroll",
                "dx": 1,
                "dy": 0
            }
        ]
        
        result = self.config_manager._validate_actions(valid_actions)
        self.assertTrue(result)
    
    def test_validate_actions_invalid_type(self):
        """Test validation of actions with invalid type."""
        invalid_actions = [
            {
                "type": "invalid_type",
                "abs_x": 100,
                "abs_y": 200
            }
        ]
        
        result = self.config_manager._validate_actions(invalid_actions)
        self.assertFalse(result)
    
    def test_validate_actions_missing_fields(self):
        """Test validation of actions with missing required fields."""
        invalid_actions = [
            {
                "type": "click",
                # Missing monitor, abs_x, abs_y, button
            }
        ]
        
        result = self.config_manager._validate_actions(invalid_actions)
        self.assertFalse(result)
    
    def test_validate_actions_invalid_wait_seconds(self):
        """Test validation of wait action with invalid seconds."""
        invalid_actions = [
            {
                "type": "wait",
                "seconds": -1.0  # Negative seconds
            }
        ]
        
        result = self.config_manager._validate_actions(invalid_actions)
        self.assertFalse(result)
    
    def test_validate_actions_not_list(self):
        """Test validation when actions is not a list."""
        result = self.config_manager._validate_actions("not a list")
        self.assertFalse(result)
    
    def test_validate_config_valid(self):
        """Test validation of valid config."""
        valid_config = {
            "meta": {
                "name": "test",
                "author": "test"
            },
            "actions": [
                {
                    "type": "click",
                    "monitor": 1,
                    "abs_x": 100,
                    "abs_y": 200,
                    "button": "left"
                }
            ]
        }
        
        result = self.config_manager._validate_config(valid_config)
        self.assertTrue(result)
    
    def test_validate_config_invalid_structure(self):
        """Test validation of config with invalid structure."""
        invalid_config = {
            "invalid_structure": True
        }
        
        result = self.config_manager._validate_config(invalid_config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_actions(self):
        """Test validation of config with invalid actions."""
        invalid_config = {
            "meta": {
                "name": "test"
            },
            "actions": [
                {
                    "type": "invalid_type"
                }
            ]
        }
        
        result = self.config_manager._validate_config(invalid_config)
        self.assertFalse(result)
    
    def test_export_macro_success(self):
        """Test successful macro export."""
        # Save a macro first
        self.config_manager.save_macro(
            self.test_actions,
            "test_macro",
            self.test_metadata
        )
        
        # Export it
        export_path = os.path.join(self.temp_dir, "exported_macro.json")
        result = self.config_manager.export_macro("test_macro", export_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check exported content
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['meta']['name'], 'test_macro')
        self.assertEqual(len(data['actions']), len(self.test_actions))
    
    def test_export_macro_nonexistent(self):
        """Test exporting non-existent macro."""
        export_path = os.path.join(self.temp_dir, "exported_macro.json")
        result = self.config_manager.export_macro("nonexistent_macro", export_path)
        
        self.assertFalse(result)
        self.assertFalse(os.path.exists(export_path))
    
    def test_import_macro_success(self):
        """Test successful macro import."""
        # Create a macro file to import
        import_data = {
            "meta": {
                "name": "imported_macro",
                "description": "Imported macro"
            },
            "actions": [
                {
                    "type": "click",
                    "monitor": 1,
                    "abs_x": 300,
                    "abs_y": 400,
                    "button": "right"
                }
            ]
        }
        
        import_path = os.path.join(self.temp_dir, "to_import.json")
        with open(import_path, 'w') as f:
            json.dump(import_data, f)
        
        # Import it
        result = self.config_manager.import_macro(import_path, "imported_macro")
        
        self.assertTrue(result)
        
        # Check that macro was imported
        config = self.config_manager.load_macro("imported_macro")
        self.assertIsNotNone(config)
        self.assertEqual(config['meta']['name'], 'imported_macro')
        self.assertEqual(len(config['actions']), 1)
        self.assertEqual(config['actions'][0]['abs_x'], 300)
    
    def test_import_macro_nonexistent(self):
        """Test importing non-existent macro file."""
        result = self.config_manager.import_macro("/nonexistent/path.json")
        self.assertFalse(result)
    
    def test_import_macro_invalid(self):
        """Test importing invalid macro file."""
        # Create invalid macro file
        import_path = os.path.join(self.temp_dir, "invalid_import.json")
        with open(import_path, 'w') as f:
            f.write("invalid content")
        
        result = self.config_manager.import_macro(import_path)
        self.assertFalse(result)
    
    def test_get_config_directory(self):
        """Test getting config directory."""
        config_dir = self.config_manager.get_config_directory()
        
        self.assertIsInstance(config_dir, Path)
        self.assertEqual(config_dir, self.config_manager.config_dir)


if __name__ == '__main__':
    unittest.main()