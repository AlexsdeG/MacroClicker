# Contributing to MacroPosFlow

Thank you for your interest in contributing to MacroPosFlow! This document provides guidelines and instructions for contributors.

## Code of Conduct

Please be respectful and considerate in all interactions. We follow the standard open source code of conduct - be inclusive, friendly, and professional.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/MacroPosFlow.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Create a new branch: `git checkout -b feature/your-feature-name`

## Coding Style

We follow **PEP 8** style guidelines with the following additional conventions:

### Python Style

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (compatible with Black formatter)
- Use type hints where appropriate
- Use docstrings for all public functions and classes
- Use meaningful variable and function names

```python
"""
Good example of a function with type hints and docstring.
"""
def calculate_relative_position(x: int, y: int, monitor_width: int, monitor_height: int) -> tuple[float, float]:
    """
    Calculate relative position within monitor bounds.
    
    Args:
        x: Absolute x coordinate
        y: Absolute y coordinate
        monitor_width: Width of the monitor
        monitor_height: Height of the monitor
    
    Returns:
        Tuple of (relative_x, relative_y) as floats between 0.0 and 1.0
    """
    rel_x = x / monitor_width
    rel_y = y / monitor_height
    return (rel_x, rel_y)
```

### Import Style

- Group imports: standard library, third-party, local application
- Use absolute imports for application modules
- Avoid wildcard imports

```python
# Standard library imports
import threading
import time
from typing import Dict, List, Optional

# Third-party imports
import numpy as np
from pynput import keyboard, mouse

# Local application imports
from macroposflow.display_manager import DisplayManager
from macroposflow.executor import ActionExecutor
```

### Error Handling

- Use specific exception types
- Include descriptive error messages
- Log errors appropriately

```python
try:
    result = some_operation()
except ValueError as e:
    logger.error(f"Invalid value provided: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error during operation: {e}")
    raise MacroPosFlowError("Operation failed") from e
```

## Testing Guidelines

- Write unit tests for all new features
- Use `pytest` for testing
- Mock external dependencies (pyautogui, pynput, etc.)
- Test both success and error cases
- Aim for high test coverage

```python
import pytest
from unittest.mock import Mock, patch
from macroposflow.executor import ActionExecutor

def test_executor_click_action():
    """Test that executor correctly processes click actions."""
    executor = ActionExecutor()
    
    with patch('pyautogui.click') as mock_click:
        action = {
            "type": "click",
            "monitor": 1,
            "rel_x": 0.5,
            "rel_y": 0.5,
            "button": "left",
            "delay": 0.1
        }
        
        executor.execute_action(action)
        mock_click.assert_called_once()
```

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Write or update tests as needed
3. Update documentation if applicable
4. Ensure all tests pass: `pytest tests/`
5. Update the README.md with new features if applicable
6. Create a pull request with a clear description of changes

## Commit Messages

Use clear and descriptive commit messages:

```
feat: add multi-monitor support
fix: resolve coordinate calculation issue
docs: update installation instructions
test: add unit tests for executor module
```

## Issue Reporting

When reporting bugs or suggesting features:

1. Use the GitHub issue tracker
2. Provide clear steps to reproduce bugs
3. Include your operating system and Python version
4. For bugs, include error messages and stack traces

## Development Phases

We follow a phased development approach as outlined in [plan.md](plan.md). Please reference the current phase when contributing new features.

## Questions?

If you have any questions about contributing, feel free to open an issue or contact the maintainers.

Happy coding! 🚀