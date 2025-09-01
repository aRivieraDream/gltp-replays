# TagPro Bot - Refactored Structure

This directory contains the refactored TagPro bot code, broken down into modular components for better maintainability and organization.

## File Structure

### Core Files
- `main.py` - Main entry point that orchestrates all components
- `tagpro_bot.py` - Main bot class that manages game lobby and coordinates components
- `driver_adapter.py` - WebDriver management and WebSocket communication
- `chat_handler.py` - Chat message processing and command handling
- `settings_manager.py` - Configuration and settings management

### Configuration and Utilities
- `constants.py` - All hardcoded values, URLs, messages, and configuration
- `utils.py` - Utility functions for time formatting, logging, and helper operations

### Dependencies
- `maps.py` - Map management (existing file)
- `replay_manager.py` - Replay handling (existing file)
- `requirements.txt` - Python dependencies (existing file)

### Organization
- `tests/` - Test files and test runner
- `logs/` - Log files, settings, and replay data

## Key Improvements

### 1. Separation of Concerns
Each class now has a single responsibility:
- **DriverAdapter**: WebDriver setup and WebSocket communication
- **ChatHandler**: Chat message processing and command execution
- **SettingsManager**: Configuration management and validation
- **TagproBot**: Main bot logic and game state management

### 2. Centralized Configuration
All hardcoded values are now in `constants.py`:
- Base URLs and endpoints
- Default settings
- User lists (moderators, restricted names)
- Periodic messages
- Browser configuration
- Timing constants

### 3. Utility Functions
Common operations are now in `utils.py`:
- Time formatting functions
- Settings file I/O
- Map filtering logic
- Game information formatting

### 4. Better Error Handling
Each component has its own error handling and logging.

## Usage

### Running the Bot

#### Option 1: Using the provided script (recommended)
```bash
./run_bot.sh
```

#### Option 2: Manual activation
```bash
# Navigate to the service directory
cd /Users/pierce/Projects/service

# Activate the virtual environment
source venv/bin/activate

# Navigate to bot directory and run
cd pythonScripts/bot
python main.py
```

#### Option 3: Direct execution (if venv is already activated)
```bash
python main.py
```

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test
python tests/test_imports.py
```

### Configuration
Settings are automatically loaded from `bot_settings.json` on startup. If the file doesn't exist, default settings are used.

### Adding New Commands
1. Add the command logic to `ChatHandler` class
2. Update the help message in `constants.py` if needed
3. Add any new constants to `constants.py`

### Modifying Settings
1. Update default values in `constants.py`
2. Modify validation logic in `SettingsManager` if needed
3. Settings are automatically saved when changed

## Migration from Original Code

The original `leader.py` file has been completely refactored. All functionality has been preserved but is now organized into logical components:

- **Original DriverAdapter class** → `driver_adapter.py`
- **Original TagproBot class** → `tagpro_bot.py` + `chat_handler.py` + `settings_manager.py`
- **Utility functions** → `utils.py`
- **Constants and configuration** → `constants.py`

## Benefits

1. **Maintainability**: Each file has a clear purpose and is easier to modify
2. **Testability**: Components can be tested independently
3. **Readability**: Code is organized logically and easier to understand
4. **Extensibility**: New features can be added without affecting existing code
5. **Configuration**: All settings are centralized and easy to modify

## File Descriptions

### `main.py`
Simple entry point that initializes the WebDriver adapter and starts the bot.

### `constants.py`
Contains all configuration values:
- URLs and endpoints
- Default settings for maps and lobby
- User lists (moderators, restricted names)
- Periodic messages for bot communication
- Browser configuration options
- Timing constants for various operations

### `utils.py`
Utility functions used across the application:
- Logger setup
- Time formatting functions
- Settings file I/O operations
- Map filtering logic
- Game information formatting

### `driver_adapter.py`
Handles all WebDriver-related operations:
- Chrome browser setup with platform-specific paths
- WebSocket message interception and processing
- DOM element interaction
- Game state detection

### `settings_manager.py`
Manages bot configuration:
- Loading/saving settings from JSON files
- Settings validation
- Map filtering based on settings
- Random preset selection

### `chat_handler.py`
Processes chat messages and commands:
- Command parsing and execution
- User authentication and permissions
- Chat message formatting
- Member management

### `tagpro_bot.py`
Main bot logic and game state management:
- Game lobby management
- Game state tracking
- Preset loading and game launching
- Main bot loop coordination
