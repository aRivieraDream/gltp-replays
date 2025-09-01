# TagPro Bot File Organization

This document explains the new file organization for the TagPro bot.

## Directory Structure

```
pythonScripts/bot/
├── main.py                    # Main entry point
├── tagpro_bot.py             # Main bot logic
├── driver_adapter.py         # WebDriver management
├── chat_handler.py           # Chat processing
├── settings_manager.py       # Configuration management
├── constants.py              # All constants and config
├── utils.py                  # Utility functions
├── maps.py                   # Map management (shared)
├── replay_manager.py         # Replay handling (shared)
├── requirements.txt          # Python dependencies
├── run_bot.sh               # Convenient run script
├── README_REFACTORED.md      # Main documentation
├── DEPLOYMENT.md            # Deployment guide
├── ORGANIZATION.md          # This file
├── leader.py                # Original file (backup)
│
├── tests/                   # Test files
│   ├── run_tests.py        # Test runner
│   └── test_imports.py     # Import verification
│
└── logs/                   # Logs and data
    ├── events.txt          # Event logs
    ├── ws.txt              # WebSocket logs
    ├── bot_settings.json   # Bot settings
    ├── replay_stats.json   # Replay statistics
    └── replay_uuids.txt    # Replay UUIDs
```

## File Categories

### Core Application Files
These are the main application files that contain the bot logic:

- **`main.py`** - Entry point that orchestrates all components
- **`tagpro_bot.py`** - Main bot class with game state management
- **`driver_adapter.py`** - WebDriver setup and WebSocket communication
- **`chat_handler.py`** - Chat message processing and commands
- **`settings_manager.py`** - Configuration and settings management

### Configuration and Utilities
These files contain configuration and helper functions:

- **`constants.py`** - All hardcoded values, URLs, messages, settings
- **`utils.py`** - Utility functions for logging, time formatting, etc.

### Dependencies
These are shared files used by the bot:

- **`maps.py`** - Map management functionality
- **`replay_manager.py`** - Replay handling functionality
- **`requirements.txt`** - Python package dependencies

### Documentation
Documentation and guides:

- **`README_REFACTORED.md`** - Main documentation
- **`DEPLOYMENT.md`** - Deployment instructions
- **`ORGANIZATION.md`** - This file

### Scripts
Convenience scripts:

- **`run_bot.sh`** - Script to run bot with venv activated

## Test Directory (`tests/`)

Contains all test-related files:

- **`run_tests.py`** - Test runner that executes all tests
- **`test_imports.py`** - Verifies all imports work correctly

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test
python tests/test_imports.py
```

## Logs Directory (`logs/`)

Contains all log files and data:

- **`events.txt`** - Bot event logs
- **`ws.txt`** - WebSocket communication logs
- **`bot_settings.json`** - Bot configuration settings
- **`replay_stats.json`** - Replay statistics data
- **`replay_uuids.txt`** - List of replay UUIDs

### Log Management

- Log files are automatically created in the `logs/` directory
- Settings files are saved to `logs/bot_settings.json`
- All logs use consistent formatting with timestamps

## Benefits of This Organization

1. **Clean Separation**: Core code, tests, and logs are clearly separated
2. **Easy Testing**: All tests are in one place with a simple runner
3. **Centralized Logging**: All logs and data are organized in one directory
4. **Better Maintenance**: Files are organized by purpose and function
5. **Docker Ready**: Structure works seamlessly with Docker deployment

## Migration Notes

- The original `leader.py` file is kept as a backup
- All log files are now automatically placed in the `logs/` directory
- Settings are saved to `logs/bot_settings.json`
- Tests can be run from the `tests/` directory

## Running the Bot

### Local Development
```bash
# Using the provided script
./run_bot.sh

# Manual activation
cd /Users/pierce/Projects/service
source venv/bin/activate
cd pythonScripts/bot
python main.py
```

### Docker Deployment
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f bot
```

The new organization makes the codebase much cleaner and easier to maintain while preserving all functionality.
