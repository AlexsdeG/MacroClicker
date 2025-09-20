# MacroPosFlow

A modular Python project that records & replays mouse/keyboard actions with advanced state management, configurable key bindings, and comprehensive control features.

## Features

- 🖱️ Record and replay mouse clicks and keyboard inputs
- ⏱️ Configurable delays between actions
- 🚨 Global emergency stop with multiple kill switches
- 💾 Save/load action sequences as JSON with metadata
- 🖥️ Multi-monitor support with relative coordinates
- 🔍 Fast pixel/area detection (mss + numpy)
- 📝 Optional OCR text detection (pytesseract)
- 🎛️ Pluggable CLI interface with multiple backends
- 🧪 Comprehensive test suite
- 🔄 Loop execution with configurable repeat counts
- ⏸️ Pause/resume functionality for both recording and execution
- 🔧 Configurable key bindings saved in settings
- 📊 Advanced state management (Stopped/Running/Paused)
- 🎲 Mouse movement randomness and smoothing options
- ⚙️ Comprehensive settings management system

## Current Status

**Phase 1: Minimal Working Prototype (MVP)** ✅ COMPLETED

- [x] Implement recorder module (F3 hotkey)
- [x] Implement executor module (action replay)
- [x] Implement CLI menu functionality
- [x] Add config module (JSON save/load)
- [x] Add global emergency stop (Esc key)

**Phase 2: Advanced Features & State Management** ✅ COMPLETED

- [x] Advanced state management (Stopped/Running/Paused)
- [x] Configurable key bindings system
- [x] Loop execution with configurable repeat counts
- [x] Pause/resume functionality for recording and execution
- [x] Enhanced key combination support
- [x] Settings management system
- [x] Multiple emergency stop mechanisms
- [x] Mouse movement randomness and smoothing
- [x] Comprehensive test suite
- [x] Advanced CLI with submenus
- [x] Real-time feedback and progress tracking

**Next Phase: Phase 3 - Multi-monitor & Advanced Vision**

- [ ] Multi-monitor coordinate system
- [ ] Pixel and area detection
- [ ] Template matching with OpenCV
- [ ] Advanced OCR integration

## Phase 2 Completion Summary

✅ **Successfully completed Phase 2 - Advanced Features & State Management**

The project now has a comprehensive advanced feature set with:

### 🎯 **Core Functionality**
- **Advanced State Management**: Proper state machines for recording and execution with Stopped/Running/Paused states
- **Configurable Key Bindings**: Fully customizable hotkeys for all operations saved in settings.json
- **Loop Execution**: Execute sequences multiple times with configurable repeat counts
- **Pause/Resume**: Pause and resume both recording and execution at any time
- **Enhanced Recording**: Multiple ways to record actions including position hotkeys and alternative clicks
- **Advanced Execution**: Support for loops, pause/resume, and multiple emergency stop mechanisms

### 🛠️ **Technical Implementation**
- **Settings Management**: Comprehensive settings system with JSON storage and import/export
- **State Manager**: Thread-safe state management with proper transitions and callbacks
- **Global Key Handler**: Advanced hotkey system supporting complex key combinations
- **Enhanced Recorder**: State-aware recording with multiple input methods
- **Enhanced Executor**: Loop support, pause/resume, progress tracking, and advanced timing
- **CLI System**: Multi-level menu system with comprehensive functionality
- **Integration**: Seamless integration between all components with proper error handling

### 🎮 **User Experience**
- **Intuitive Controls**: Configurable hotkeys for all operations
- **Visual Feedback**: Real-time feedback during recording and execution with progress tracking
- **State Awareness**: Clear indication of current system state and available actions
- **Flexible Recording**: Multiple ways to capture actions (hotkeys, clicks, alternative methods)
- **Advanced Execution**: Loop control, pause/resume, and multiple stop mechanisms
- **Settings Management**: Easy configuration of all aspects of the system
- **Comprehensive UI**: Organized menu system with logical grouping of features

### 📊 **Advanced Features**
- **State Machines**: Proper state management for both recording and execution
- **Key Bindings**: Fully configurable hotkeys with modifier support
- **Loop Control**: Execute sequences multiple times with progress tracking
- **Pause/Resume**: Full control over recording and execution timing
- **Emergency Stops**: Multiple ways to stop operations (global, process-specific)
- **Randomness**: Configurable mouse movement randomness for natural execution
- **Smoothing**: Optional mouse movement smoothing for realistic playback
- **Settings Persistence**: All settings saved and loaded automatically

### 🔒 **Safety Features**
- **Multiple Emergency Stops**: Global Esc key, process-specific kill switches
- **State Validation**: Prevents invalid state transitions and operations
- **Dry Run Mode**: Test without actual mouse/keyboard input
- **Input Validation**: Comprehensive validation of all actions and settings
- **Thread Safety**: Safe concurrent operations with proper locking
- **Cleanup Procedures**: Proper resource cleanup and state reset

## Key Bindings

### Default Configuration

The system comes with configurable key bindings that can be customized in the settings:

#### 🎙️ **Recording Controls**
- **Start/Stop Recording**: `Ctrl + F8`
- **Pause/Resume Recording**: `Ctrl + F9`
- **Record Position**: `Ctrl + F10` (records mouse position without clicking)
- **Alternative Click**: `Ctrl + Right Mouse` (records left click at position)

#### ▶️ **Execution Controls**
- **Start/Stop Execution**: `Ctrl + F8`
- **Pause/Resume Execution**: `Ctrl + F9`
- **Emergency Kill**: `Ctrl + Shift + Esc`

#### 🌐 **Global Controls**
- **Global Emergency Stop**: `Esc` (stops both recording and execution)

### Key Binding Features

- **Modifier Support**: Full support for Ctrl, Alt, Shift, and Win/Cmd modifiers
- **Combination Detection**: Advanced detection of key combinations
- **Customizable**: All key bindings can be changed through the settings menu
- **Persistent**: Key bindings are saved automatically and loaded on startup
- **Conflict Prevention**: System prevents conflicts between different functions

## State Management

### Process States

Both recording and execution processes have three possible states:

#### 🛑 **STOPPED**
- Initial state for all processes
- No active operations
- Resources are released
- Can transition to RUNNING

#### ▶️ **RUNNING**
- Actively performing operations
- Full functionality available
- Can transition to PAUSED or STOPPED
- Resources are allocated

#### ⏸️ **PAUSED**
- Temporarily suspended operations
- Timing is preserved
- Resources are held
- Can transition to RUNNING or STOPPED

### State Transitions

```
STOPPED → RUNNING → PAUSED → RUNNING → STOPPED
   ↑                                    ↓
   └────────────────────────────────────┘
```

### State Features

- **Thread-Safe**: All state changes are thread-safe with proper locking
- **Callback System**: State changes trigger callbacks for UI updates
- **Validation**: Invalid state transitions are prevented
- **Timing Tracking**: Accurate timing including pause durations
- **Information Tracking**: Comprehensive process information and statistics

## Settings Management

### Settings Categories

#### 🔑 **Key Bindings**
- All configurable hotkeys for recording and execution
- Supports complex key combinations with modifiers
- Persistent across application restarts

#### ⚙️ **Execution Settings**
- **Default Loop Count**: Number of times to repeat sequences (default: 1)
- **Default Delay**: Time between actions (default: 0.1s)
- **Enable Randomness**: Add random variation to mouse movements (default: False)
- **Randomness Radius**: Maximum pixel offset for random clicks (default: 5px)
- **Enable Smoothing**: Smooth mouse movements between positions (default: True)
- **Smoothing Duration**: Time for movement smoothing (default: 0.1s)

#### 🎙️ **Recording Settings**
- **Default Delay**: Time between recorded actions (default: 0.1s)
- **Auto Timestamp**: Automatically add timestamps to actions (default: True)
- **Real-time Feedback**: Show feedback during recording (default: True)

#### 🖥️ **UI Settings**
- **Show Action Count**: Display number of actions in UI (default: True)
- **Show Timing Info**: Display timing information (default: True)
- **Confirm Destructive Actions**: Confirm before destructive operations (default: True)
- **Verbose Logging**: Enable detailed logging (default: False)

### Settings Features

- **JSON Storage**: Settings stored in human-readable JSON format
- **Import/Export**: Settings can be exported and imported
- **Default Reset**: Easy reset to default values
- **Validation**: All settings are validated before application
- **Runtime Updates**: Settings can be changed without restarting

## Advanced Usage

### Phase 2 Workflow

#### 1. **Recording Session**
```
1. Select "Recording" → "Start Recording Session"
2. System prepares recording but waits for your signal
3. Press Ctrl+F8 to actually start recording
4. Use any of these methods to record:
   - Click normally to record clicks
   - Press Ctrl+F10 to record mouse position
   - Press Ctrl+Right Click for alternative click
   - Type keys or key combinations
5. Use Ctrl+F9 to pause/resume recording
6. Press Ctrl+F8 to stop recording
7. Review and save your recorded sequence
```

#### 2. **Execution Session**
```
1. Load or record a sequence of actions
2. Select "Execution" → "Run Current Sequence"
3. Configure loop count (default from settings)
4. Press Enter to start execution
5. Use these controls during execution:
   - Ctrl+F8 to stop execution
   - Ctrl+F9 to pause/resume execution
   - Ctrl+Shift+Esc for emergency kill
   - Esc for global emergency stop
6. Monitor progress and completion
```

#### 3. **Configuration**
```
1. Select "Settings" to access all configuration options
2. View current key bindings and settings
3. Modify execution parameters (loops, randomness, smoothing)
4. Customize key bindings if needed
5. Reset to defaults if desired
6. All changes are saved automatically
```

### Advanced Features

#### **Loop Execution**
- Execute sequences multiple times automatically
- Configurable repeat count with progress tracking
- Each loop is tracked separately
- Can be paused/resumed during execution

#### **Pause/Resume Functionality**
- Pause recording to prepare next actions
- Pause execution to take breaks or intervene
- Timing is preserved during pauses
- Resume from exactly where you left off

#### **Multiple Recording Methods**
- Normal click recording
- Position recording without clicking
- Alternative click methods
- Full keyboard and combination support

#### **Emergency Stop System**
- Global Esc key for immediate stop
- Process-specific kill switches
- Multiple layers of safety
- Clean state reset after stops

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

# Run the test suite
python -m macroposflow.test_phase2
```

### Advanced Usage Examples

#### **Custom Settings**
```bash
# The application automatically creates settings.json
# Edit the file directly or use the settings menu
# Key bindings can be customized for your preferences
```

#### **Testing Functionality**
```bash
# Run comprehensive tests
python test_phase2.py

# Tests cover:
# - Settings management
# - State management
# - Key bindings
# - Recording and execution
# - Integration between components
```

## Dependencies

### Core Dependencies
- `pyautogui` - Mouse and keyboard control
- `pynput` - Global hotkey listener
- `mss` - Fast screen capture
- `numpy` - Numerical operations for vision
- `console-menu` - CLI interface
- `simple-term-menu` - Alternative CLI interface

### Optional Dependencies
- `pytesseract` - OCR support
- `opencv-python` - Template matching and advanced vision
- `pillow` - Image processing (required for OCR)

### Development Dependencies
- `pytest` - Testing framework
- `pytest-mock` - Mocking support for tests

## Project Structure

```
macroposflow/
├── __init__.py
├── main.py                 # Entry point
├── settings.py             # Settings management system
├── state_manager.py        # State management system
├── recorder.py             # Action recording with advanced features
├── executor.py             # Action execution with loops and pause
├── config.py               # Configuration management
├── cli/                    # CLI adapters
│   ├── __init__.py
│   └── consolemenu_cli.py  # Advanced CLI with submenus
├── tests/                  # Test suite
│   ├── test_phase2.py      # Comprehensive Phase 2 tests
│   ├── test_basic.py       # Basic tests
│   └── assets/             # Test images
├── macros/                 # Sample macros
│   └── sample.json          # Example macro
└── settings.json           # Default settings configuration
```

## Testing

### Running Tests

```bash
# Run comprehensive Phase 2 tests
python test_phase2.py

# Run specific test categories
pytest tests/test_basic.py
pytest tests/test_recorder.py
pytest tests/test_executor.py
```

### Test Coverage

The comprehensive test suite covers:
- **Settings Management**: Load, save, import, export functionality
- **State Management**: State transitions, validation, callbacks
- **Key Bindings**: Combination detection, customization
- **Recording**: Advanced recording with state management
- **Execution**: Loop execution, pause/resume, progress tracking
- **Integration**: Full workflow testing and component interaction

## Development

### Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd MacroPosFlow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
python test_phase2.py

# Run the application
python -m macroposflow
```

## Configuration Files

### settings.json
Created automatically on first run, contains all user preferences:
- Key bindings for all operations
- Execution parameters (loops, randomness, smoothing)
- Recording preferences
- UI settings

### Macro Files
Stored in JSON format with:
- Action sequences with timing
- Metadata (name, description, creation date)
- Action count and total duration

## Roadmap

See [plan.md](plan.md) for detailed phased implementation plan.

### Phase 3 Preview
- Multi-monitor coordinate system
- Pixel and area detection
- Template matching with OpenCV
- Advanced OCR integration
- GUI interface option

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **pynput** library for global hotkey support
- **pyautogui** for mouse and keyboard control
- **console-menu** for CLI interface
- **mss** for fast screen capture
- All contributors and testers who helped make Phase 2 a reality