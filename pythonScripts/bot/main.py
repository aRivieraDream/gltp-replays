#!/usr/bin/env python3
"""
Main entry point for the TagPro bot.
This file orchestrates all the refactored components.
"""

from driver_adapter import DriverAdapter
from tagpro_bot import TagproBot


def main():
    """Main function to start the TagPro bot."""
    try:
        # Initialize the WebDriver adapter
        adapter = DriverAdapter()
        
        # Create and run the bot
        bot = TagproBot(adapter)
        bot.run()
        
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Bot crashed with error: {e}")
        raise


if __name__ == '__main__':
    main()
