"""
Basic tests for MacroPosFlow.

This module contains basic tests to ensure the project structure is working correctly.
"""

import sys
import os
import json

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macroposflow import __version__


def test_package_version():
    """Test that the package has a version."""
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_import_main():
    """Test that we can import the main module."""
    from macroposflow.main import main
    assert callable(main)


def test_import_cli():
    """Test that we can import the CLI module."""
    from macroposflow.cli import ConsoleMenuCLI
    assert ConsoleMenuCLI is not None


def test_sample_macro_exists():
    """Test that the sample macro file exists."""
    macro_path = os.path.join(os.path.dirname(__file__), '..', 'macros', 'sample.json')
    assert os.path.exists(macro_path), "Sample macro file should exist"


def test_sample_macro_valid_json():
    """Test that the sample macro is valid JSON."""
    macro_path = os.path.join(os.path.dirname(__file__), '..', 'macros', 'sample.json')
    
    with open(macro_path, 'r') as f:
        try:
            data = json.load(f)
            assert 'meta' in data
            assert 'actions' in data
            assert isinstance(data['actions'], list)
        except json.JSONDecodeError:
            assert False, "Sample macro should be valid JSON"


if __name__ == "__main__":
    """Run all tests when script is executed directly."""
    print('Running basic tests...')
    
    tests = [
        test_package_version,
        test_import_main,
        test_import_cli,
        test_sample_macro_exists,
        test_sample_macro_valid_json
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f'✓ {test.__name__} passed')
            passed += 1
        except Exception as e:
            print(f'✗ {test.__name__} failed: {e}')
            failed += 1
    
    print(f'\nTest Results: {passed} passed, {failed} failed')
    
    if failed == 0:
        print('All tests passed! 🎉')
    else:
        print('Some tests failed. 😞')
        sys.exit(1)