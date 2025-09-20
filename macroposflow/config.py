"""
Configuration module for MacroPosFlow.

This module provides functionality to save and load macro configurations
as JSON files, along with global settings management.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import pathlib

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages macro configurations and global settings.
    
    This class provides functionality to save and load macro configurations
    as JSON files, with validation and error handling.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_dir: Directory to store configuration files.
                       If None, uses default macros directory.
        """
        if config_dir is None:
            # Default to macros directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(current_dir, 'macros')
        
        self.config_dir = pathlib.Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Global settings
        self.global_settings = {
            'default_delay': 0.1,
            'emergency_stop_key': 'esc',
            'record_hotkey': 'f3',
            'dry_run': False,
            'log_level': 'INFO',
            'mouse_speed': 1.0,
            'click_delay': 0.1
        }
        
        # Load global settings if they exist
        self._load_global_settings()
        
        logger.info(f"ConfigManager initialized with config directory: {self.config_dir}")
    
    def save_macro(self, actions: List[Dict[str, Any]], 
                   filename: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a macro configuration to a JSON file.
        
        Args:
            actions: List of actions to save
            filename: Name of the file to save (without extension)
            metadata: Optional metadata dictionary
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.config_dir / filename
            
            # Create metadata if not provided
            if metadata is None:
                metadata = {}
            
            # Add default metadata fields
            metadata.setdefault('name', filename.replace('.json', ''))
            metadata.setdefault('created', datetime.now().isoformat())
            metadata.setdefault('version', '1.0')
            metadata.setdefault('author', 'MacroPosFlow')
            metadata.setdefault('description', 'Macro recorded with MacroPosFlow')
            
            # Create the configuration object
            config = {
                'meta': metadata,
                'actions': actions,
                'settings': self.global_settings.copy()
            }
            
            # Validate actions before saving
            if not self._validate_actions(actions):
                logger.error("Invalid actions - cannot save macro")
                return False
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved macro to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving macro to {filename}: {e}")
            return False
    
    def load_macro(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a macro configuration from a JSON file.
        
        Args:
            filename: Name of the file to load (with or without .json extension)
            
        Returns:
            Dictionary containing the macro configuration, or None if loading failed
        """
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.config_dir / filename
            
            if not filepath.exists():
                logger.error(f"Macro file not found: {filepath}")
                return None
            
            # Load from file
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate configuration structure
            if not self._validate_config(config):
                logger.error(f"Invalid configuration structure in {filename}")
                return None
            
            logger.info(f"Loaded macro from {filepath}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading macro from {filename}: {e}")
            return None
    
    def list_macros(self) -> List[str]:
        """
        List all available macro files.
        
        Returns:
            List of macro filenames (without .json extension)
        """
        try:
            macro_files = []
            for filepath in self.config_dir.glob('*.json'):
                macro_files.append(filepath.stem)
            
            macro_files.sort()
            logger.info(f"Found {len(macro_files)} macro files")
            return macro_files
            
        except Exception as e:
            logger.error(f"Error listing macros: {e}")
            return []
    
    def delete_macro(self, filename: str) -> bool:
        """
        Delete a macro file.
        
        Args:
            filename: Name of the file to delete (with or without .json extension)
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.config_dir / filename
            
            if not filepath.exists():
                logger.error(f"Macro file not found: {filepath}")
                return False
            
            filepath.unlink()
            logger.info(f"Deleted macro file: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting macro {filename}: {e}")
            return False
    
    def get_macro_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata information about a macro without loading the full configuration.
        
        Args:
            filename: Name of the macro file (with or without .json extension)
            
        Returns:
            Dictionary containing macro metadata, or None if loading failed
        """
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.config_dir / filename
            
            if not filepath.exists():
                logger.error(f"Macro file not found: {filepath}")
                return None
            
            # Load only the metadata section
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            metadata = config.get('meta', {})
            action_count = len(config.get('actions', []))
            
            # Add computed metadata
            metadata['action_count'] = action_count
            metadata['file_size'] = filepath.stat().st_size
            metadata['file_modified'] = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting macro info for {filename}: {e}")
            return None
    
    def save_global_settings(self) -> bool:
        """
        Save global settings to a configuration file.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            settings_file = self.config_dir / 'settings.json'
            
            settings_config = {
                'global_settings': self.global_settings,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved global settings to {settings_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving global settings: {e}")
            return False
    
    def _load_global_settings(self) -> None:
        """Load global settings from configuration file."""
        try:
            settings_file = self.config_dir / 'settings.json'
            
            if not settings_file.exists():
                logger.info("No global settings file found, using defaults")
                return
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings_config = json.load(f)
            
            loaded_settings = settings_config.get('global_settings', {})
            
            # Update global settings with loaded values
            self.global_settings.update(loaded_settings)
            
            logger.info("Loaded global settings")
            
        except Exception as e:
            logger.error(f"Error loading global settings: {e}")
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a global setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.global_settings.get(key, default)
    
    def set_global_setting(self, key: str, value: Any) -> None:
        """
        Set a global setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.global_settings[key] = value
        logger.debug(f"Set global setting {key} = {value}")
    
    def get_global_settings(self) -> Dict[str, Any]:
        """
        Get a copy of all global settings.
        
        Returns:
            Dictionary of global settings
        """
        return self.global_settings.copy()
    
    def update_global_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update multiple global settings.
        
        Args:
            settings: Dictionary of settings to update
        """
        self.global_settings.update(settings)
        logger.debug(f"Updated global settings: {settings}")
    
    def _validate_actions(self, actions: List[Dict[str, Any]]) -> bool:
        """
        Validate a list of actions.
        
        Args:
            actions: List of actions to validate
            
        Returns:
            True if actions are valid, False otherwise
        """
        if not isinstance(actions, list):
            logger.error("Actions must be a list")
            return False
        
        valid_action_types = {'click', 'wait', 'keypress', 'scroll'}
        
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                logger.error(f"Action {i} must be a dictionary")
                return False
            
            action_type = action.get('type')
            if not action_type:
                logger.error(f"Action {i} missing 'type' field")
                return False
            
            if action_type not in valid_action_types:
                logger.error(f"Action {i} has invalid type: {action_type}")
                return False
            
            # Validate specific action types
            if action_type == 'click':
                required_fields = ['monitor', 'abs_x', 'abs_y', 'button']
                for field in required_fields:
                    if field not in action:
                        logger.error(f"Click action {i} missing required field: {field}")
                        return False
            
            elif action_type == 'wait':
                if 'seconds' not in action:
                    logger.error(f"Wait action {i} missing 'seconds' field")
                    return False
                
                if not isinstance(action['seconds'], (int, float)) or action['seconds'] < 0:
                    logger.error(f"Wait action {i} has invalid seconds value")
                    return False
            
            elif action_type == 'keypress':
                if 'key' not in action:
                    logger.error(f"Keypress action {i} missing 'key' field")
                    return False
            
            elif action_type == 'scroll':
                if 'dx' not in action and 'dy' not in action:
                    logger.error(f"Scroll action {i} missing 'dx' or 'dy' field")
                    return False
        
        logger.debug(f"Validated {len(actions)} actions")
        return True
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate a macro configuration structure.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        if not isinstance(config, dict):
            logger.error("Configuration must be a dictionary")
            return False
        
        required_sections = ['meta', 'actions']
        for section in required_sections:
            if section not in config:
                logger.error(f"Configuration missing required section: {section}")
                return False
        
        # Validate actions
        if not self._validate_actions(config['actions']):
            return False
        
        # Validate metadata
        meta = config['meta']
        if not isinstance(meta, dict):
            logger.error("Metadata must be a dictionary")
            return False
        
        logger.debug("Configuration validation passed")
        return True
    
    def export_macro(self, filename: str, export_path: str) -> bool:
        """
        Export a macro to a specific path.
        
        Args:
            filename: Name of the macro to export
            export_path: Path to export the macro to
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            config = self.load_macro(filename)
            if config is None:
                return False
            
            export_path = pathlib.Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported macro {filename} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting macro {filename}: {e}")
            return False
    
    def import_macro(self, import_path: str, new_filename: Optional[str] = None) -> bool:
        """
        Import a macro from a specific path.
        
        Args:
            import_path: Path to import the macro from
            new_filename: New filename to save as (optional)
            
        Returns:
            True if import was successful, False otherwise
        """
        try:
            import_path = pathlib.Path(import_path)
            
            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not self._validate_config(config):
                logger.error("Invalid configuration for import")
                return False
            
            if new_filename is None:
                new_filename = import_path.stem
            
            return self.save_macro(
                config['actions'],
                new_filename,
                config['meta']
            )
            
        except Exception as e:
            logger.error(f"Error importing macro from {import_path}: {e}")
            return False
    
    def get_config_directory(self) -> pathlib.Path:
        """
        Get the configuration directory path.
        
        Returns:
            Path to the configuration directory
        """
        return self.config_dir