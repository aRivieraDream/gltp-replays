#!/bin/bash
# Script to run the TagPro bot with virtual environment activated

# Navigate to the service directory and activate virtual environment
cd /Users/pierce/Projects/service
source venv/bin/activate

# Navigate to bot directory and run the bot
cd pythonScripts/bot
python main.py
