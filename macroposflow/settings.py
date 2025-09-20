"""
Settings management module for MacroPosFlow.

This module provides functionality to manage application settings including
key bindings, default behaviors, and user preferences.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class KeyBindings:
    """Configuration for key bindings."""
    # Recording controls
    record_start_stop: List[str]  # Keys to start/stop recording (e.g., ['ctrl', 'f8'])
    record_pause_resume: List[str]  # Keys to pause/resume recording (e.g., ['ctrl', 'f9'])
    record_position: List[str]  # Keys to record position (e.g., ['ctrl', 'f10'])
    record_alt_click: List[str]  # Alternative click recording (e.g., ['ctrl', 'right'])
    
    # Execution controls
    execute_start_stop: List[str]  # Keys to start/stop execution (e.g., ['ctrl', 'f8'])
    execute_pause_resume: List[str]  # Keys to pause/resume execution (e.g., ['ctrl', 'f9'])
    execute_kill: List[str]  # Emergency kill switch (e.g., ['ctrl', 'shift', 'esc'])
    
    # Global controls
    global_emergency_stop: List[str]  # Global emergency stop (e.g., ['esc'])


@dataclass
class ExecutionSettings:
    """Configuration for execution behavior."""
    default_loop_count: int  # Default number of times to repeat execution
    default_delay: float  # Default delay between actions
    enable_randomness: bool  # Enable mouse movement randomness
    randomness_radius: int  # Radius for random click offset
    enable_smoothing: bool  # Enable mouse movement smoothing
    smoothing_duration: float  # Duration for smoothing movements


@dataclass
class RecordingSettings:
    """Configuration for recording behavior."""
    default_delay: float  # Default delay between recorded actions
    enable_auto_timestamp: bool  # Automatically add timestamps
    show_real_time_feedback: bool  # Show feedback during recording


@dataclass
class UISettings:
    """Configuration for user interface."""
    show_action_count: bool  # Show number of actions in UI
    show_timing_info: bool  # Show timing information
    confirm_destructive_actions: bool  # Confirm before destructive actions
    verbose_logging: bool  # Enable verbose logging


@dataclass
class Settings:
    """Main settings configuration."""
    key_bindings: KeyBindings
    execution: ExecutionSettings
    recording: RecordingSettings
    ui: UISettings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary."""
        key_bindings = KeyBindings(**data.get('key_bindings', {}))
        execution = ExecutionSettings(**data.get('execution', {}))
        recording = RecordingSettings(**data.get('recording', {}))
        ui = UISettings(**data.get('ui', {}))
        return cls(key_bindings, execution, recording, ui)


class SettingsManager:
    """
    Manages application settings and configuration.
    
    This class provides functionality to load, save, and manage
    application settings including key bindings and preferences.
    """
    
    def __init__(self, settings_dir: Optional[str] = None):
        """
        Initialize the SettingsManager.
        
        Args:
            settings_dir: Directory to store settings files. If None, uses default location.
        """
        if settings_dir:
            self.settings_dir = Path(settings_dir)
        else:
            # Use user's home directory or current directory
            self.settings_dir = Path.home() / '.macroposflow'
            if not self.settings_dir.exists():
                self.settings_dir = Path.cwd()
        
        self.settings_file = self.settings_dir / 'settings.json'
        self.settings: Optional[Settings] = None
        
        # Ensure settings directory exists
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SettingsManager initialized with directory: {self.settings_dir}")
    
    def get_default_settings(self) -> Settings:
        """
        Get default settings configuration.
        
        Returns:
            Default Settings object
        """
        key_bindings = KeyBindings(
            record_start_stop=['ctrl', 'f8'],
            record_pause_resume=['ctrl', 'f9'],
            record_position=['ctrl', 'f10'],
            record_alt_click=['ctrl', 'right'],
            execute_start_stop=['ctrl', 'f8'],
            execute_pause_resume=['ctrl', 'f9'],
            execute_kill=['ctrl', 'shift', 'esc'],
            global_emergency_stop=['esc']
        )
        
        execution = ExecutionSettings(
            default_loop_count=1,
            default_delay=0.1,
            enable_randomness=False,
            randomness_radius=5,
            enable_smoothing=True,
            smoothing_duration=0.1
        )
        
        recording = RecordingSettings(
            default_delay=0.1,
            enable_auto_timestamp=True,
            show_real_time_feedback=True
        )
        
        ui = UISettings(
            show_action_count=True,
            show_timing_info=True,
            confirm_destructive_actions=True,
            verbose_logging=False
        )
        
        return Settings(key_bindings, execution, recording, ui)
    
    def load_settings(self) -> Settings:
        """
        Load settings from file.
        
        Returns:
            Loaded Settings object, or default settings if file doesn't exist
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.settings = Settings.from_dict(data)
                logger.info(f"Settings loaded from {self.settings_file}")
            else:
                self.settings = self.get_default_settings()
                self.save_settings()
                logger.info("Default settings created and saved")
                
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.settings = self.get_default_settings()
        
        return self.settings
    
    def save_settings(self) -> bool:
        """
        Save current settings to file.
        
        Returns:
            True if save was successful, False otherwise
        """
        if not self.settings:
            logger.error("No settings to save")
            return False
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings saved to {self.settings_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get_settings(self) -> Settings:
        """
        Get current settings.
        
        Returns:
            Current Settings object
        """
        if not self.settings:
            return self.load_settings()
        return self.settings
    
    def update_settings(self, settings: Settings) -> bool:
        """
        Update settings and save to file.
        
        Args:
            settings: New Settings object
            
        Returns:
            True if update was successful, False otherwise
        """
        self.settings = settings
        return self.save_settings()
    
    def reset_to_defaults(self) -> bool:
        """
        Reset settings to default values.
        
        Returns:
            True if reset was successful, False otherwise
        """
        self.settings = self.get_default_settings()
        return self.save_settings()
    
    def get_key_bindings(self) -> KeyBindings:
        """
        Get current key bindings.
        
        Returns:
            Current KeyBindings object
        """
        return self.get_settings().key_bindings
    
    def update_key_bindings(self, key_bindings: KeyBindings) -> bool:
        """
        Update key bindings and save settings.
        
        Args:
            key_bindings: New KeyBindings object
            
        Returns:
            True if update was successful, False otherwise
        """
        settings = self.get_settings()
        settings.key_bindings = key_bindings
        return self.update_settings(settings)
    
    def get_execution_settings(self) -> ExecutionSettings:
        """
        Get current execution settings.
        
        Returns:
            Current ExecutionSettings object
        """
        return self.get_settings().execution
    
    def update_execution_settings(self, execution: ExecutionSettings) -> bool:
        """
        Update execution settings and save.
        
        Args:
            execution: New ExecutionSettings object
            
        Returns:
            True if update was successful, False otherwise
        """
        settings = self.get_settings()
        settings.execution = execution
        return self.update_settings(settings)
    
    def get_recording_settings(self) -> RecordingSettings:
        """
        Get current recording settings.
        
        Returns:
            Current RecordingSettings object
        """
        return self.get_settings().recording
    
    def update_recording_settings(self, recording: RecordingSettings) -> bool:
        """
        Update recording settings and save.
        
        Args:
            recording: New RecordingSettings object
            
        Returns:
            True if update was successful, False otherwise
        """
        settings = self.get_settings()
        settings.recording = recording
        return self.update_settings(settings)
    
    def get_ui_settings(self) -> UISettings:
        """
        Get current UI settings.
        
        Returns:
            Current UISettings object
        """
        return self.get_settings().ui
    
    def update_ui_settings(self, ui: UISettings) -> bool:
        """
        Update UI settings and save.
        
        Args:
            ui: New UISettings object
            
        Returns:
            True if update was successful, False otherwise
        """
        settings = self.get_settings()
        settings.ui = ui
        return self.update_settings(settings)
    
    def export_settings(self, file_path: str) -> bool:
        """
        Export current settings to a file.
        
        Args:
            file_path: Path to export settings to
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.get_settings().to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            file_path: Path to import settings from
            
        Returns:
            True if import was successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            settings = Settings.from_dict(data)
            self.settings = settings
            self.save_settings()
            
            logger.info(f"Settings imported from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False
    
    def get_settings_info(self) -> Dict[str, Any]:
        """
        Get information about current settings.
        
        Returns:
            Dictionary with settings information
        """
        settings = self.get_settings()
        return {
            'settings_file': str(self.settings_file),
            'settings_exist': self.settings_file.exists(),
            'key_bindings_count': len(settings.key_bindings.__dict__),
            'execution_settings_count': len(settings.execution.__dict__),
            'recording_settings_count': len(settings.recording.__dict__),
            'ui_settings_count': len(settings.ui.__dict__)
        }