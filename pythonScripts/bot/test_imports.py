#!/usr/bin/env python3
"""
Test script to verify all imports work correctly in the refactored structure.
"""

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test constants
        from constants import (
            BASE_URL, ROOM_NAME, DEFAULT_MAP_SETTINGS, 
            MODERATOR_NAMES, PERIODIC_MESSAGES
        )
        print("✓ constants.py imported successfully")
        
        # Test utils
        from utils import (
            setup_logger, time_since, timedelta_str, 
            default_float, get_game_info
        )
        print("✓ utils.py imported successfully")
        
        # Test driver adapter
        from driver_adapter import DriverAdapter
        print("✓ driver_adapter.py imported successfully")
        
        # Test settings manager
        from settings_manager import SettingsManager
        print("✓ settings_manager.py imported successfully")
        
        # Test chat handler
        from chat_handler import ChatHandler
        print("✓ chat_handler.py imported successfully")
        
        # Test main bot
        from tagpro_bot import TagproBot
        print("✓ tagpro_bot.py imported successfully")
        
        # Test main
        from main import main
        print("✓ main.py imported successfully")
        
        print("\nAll imports successful! The refactored structure is working correctly.")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\nReady to run the bot with: python main.py")
    else:
        print("\nPlease fix the import errors before running the bot.")
