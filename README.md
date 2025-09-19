# MacroPosFlow

A modular Python project that records & replays mouse/keyboard actions, with delays and a global emergency stop.

## Features

- 🖱️ Record and replay mouse clicks and keyboard inputs
- ⏱️ Configurable delays between actions
- 🚨 Global emergency stop (Esc key)
- 💾 Save/load action sequences as JSON
- 🖥️ Multi-monitor support with relative coordinates
- 🔍 Fast pixel/area detection
- 📝 Optional OCR text detection
- 🎛️ Pluggable CLI interface
- 🧪 Comprehensive test suite

## Current Status

**Phase 0: Project Bootstrap** ✅ COMPLETED

- [x] Repository skeleton created
- [x] Dependencies listed in requirements.txt and pyproject.toml
- [x] Basic project structure
- [x] CONTRIBUTING.md with coding guidelines
- [x] Sample macro folder with example JSON
- [x] CI skeleton (GitHub Actions)
- [x] Basic test suite (all tests passing)
- [x] Package configuration
- [x] Basic CLI placeholder implementation

**Next Phase: Phase 1 - Minimal Working Prototype (MVP)**

- [ ] Implement recorder module (F3 hotkey)
- [ ] Implement executor module (action replay)
- [ ] Implement CLI menu functionality
- [ ] Add config module (JSON save/load)
- [ ] Add global emergency stop (Esc key)

## Phase 0 Completion Summary

✅ **Successfully completed Phase 0 - Project Bootstrap**

The project now has a complete foundation with:

- **Project Structure**: Well-organized package structure following Python best practices
- **Dependencies**: All required dependencies listed in both requirements.txt and pyproject.toml
- **Documentation**: Comprehensive README.md, CONTRIBUTING.md, and development plan
- **Testing**: Basic test suite with 5 passing tests validating core functionality
- **CI/CD**: GitHub Actions workflow for automated testing
- **Package Configuration**: Proper pyproject.toml with entry points and optional dependencies
- **Sample Data**: Example macro JSON file demonstrating the expected format
- **Code Quality**: PEP 8 compliant code with proper type hints and documentation

The project is now ready for Phase 1 development with a solid foundation in place.

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd MacroPosFlow

# Install in development mode
pip install -e .

# Or install with all optional dependencies
pip install -e ".[all]"
```

### Using pip (when published)

```bash
# Basic installation
pip install macroposflow

# With OCR support
pip install macroposflow[ocr]

# With OpenCV support
pip install macroposflow[opencv]

# With all optional features
pip install macroposflow[all]
```

## Usage

### Basic Usage

```bash
# Run the application
macroposflow

# Or if installed from source
python -m macroposflow
```

## Dependencies

- `pyautogui` - Mouse and keyboard control
- `pynput` - Global hotkey listener
- `mss` - Fast screen capture
- `numpy` - Numerical operations for vision
- `pytesseract` - OCR support (optional)
- `console-menu` - CLI interface
- `pytest` - Testing framework

## Usage

### Basic Recording and Playback

1. Run the application: `python -m macroposflow`
2. Select "Record new point" from the menu
3. Press F3 to record mouse positions
4. Save your macro
5. Load and run the macro

### Emergency Stop

Press **Esc** at any time to stop macro execution immediately.

## Development

### Project Structure

```
macroposflow/
├── __init__.py
├── main.py                 # Entry point
├── cli/                    # CLI adapters
│   ├── __init__.py
│   └── consolemenu_cli.py  # Default CLI implementation
├── recorder.py             # Action recording
├── executor.py             # Action execution
├── input_control.py        # Input wrappers
├── vision.py               # Vision helpers
├── ocr_wrapper.py          # OCR functionality
├── display_manager.py      # Monitor management
├── config.py               # Configuration
├── movement.py             # Movement smoothing
├── tests/                  # Test suite
│   └── assets/             # Test images
└── macros/                 # Sample macros
```

### Running Tests

```bash
pytest tests/
```

### Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Roadmap

See [plan.md](plan.md) for detailed phased implementation plan.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.