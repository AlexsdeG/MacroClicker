"""
MacroPosFlow - A modular Python project for recording & replaying mouse/keyboard actions.

This package provides functionality to:
- Record mouse and keyboard actions
- Save and load action sequences
- Execute recorded actions with configurable delays
- Support multi-monitor environments
- Provide emergency stop functionality
"""

__version__ = "0.1.0"
__author__ = "MacroPosFlow Team"
__email__ = "contact@macroposflow.com"

from .main import main

__all__ = ["main"]