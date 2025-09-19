"""
CLI adapters for MacroPosFlow.

This package contains different CLI implementations that can be swapped
without changing the core functionality.
"""

from .consolemenu_cli import ConsoleMenuCLI

__all__ = ["ConsoleMenuCLI"]