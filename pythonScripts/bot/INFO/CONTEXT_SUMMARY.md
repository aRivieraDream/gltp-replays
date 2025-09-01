# TagPro Bot Debugging Session Summary

## Current Status (September 1, 2025)
- Bot is running in Docker container but has several issues
- User is in TagPro group waiting to join but bot isn't launching games
- Logs are visible via `docker-compose logs bot` but not syncing to host filesystem

## Key Issues Being Debugged

### 1. World Record Import Problem (ORIGINAL ISSUE)
- **Problem**: MAP command says "world record not available" for maps that have world records
- **Root Cause**: Incorrect file path in `replay_manager.py` for `replay_stats.json`
- **Fix Applied**: Changed path from `"data/replay_stats.json"` to `"../data/replay_stats.json"` for Docker container
- **Status**: Path should be correct now, needs testing

### 2. Bot Not Launching Games (NEW ISSUE AFTER FIXES)
- **Problem**: Bot cycles through presets but doesn't launch games when players are waiting
- **Suspected Cause**: `current_game_preset` is `None` when MAP command is issued
- **Debug Added**: Added debug prints in `chat_handler.py` and `tagpro_bot.py` to trace execution
- **Status**: Need to test MAP command to see debug output

### 3. Logging Issues
- **Problem**: Logs not syncing from Docker container to host filesystem
- **Volume Mapping**: Added `./pythonScripts/bot/logs:/app/bot/logs` in docker-compose.yml
- **Status**: Volume mapping not working - logs only visible via `docker-compose logs bot`

### 4. Superfluous "Setting" Messages
- **Problem**: Bot repeatedly sends "setting" messages
- **Fix Applied**: Added `self.group_configured` flag in `tagpro_bot.py` to prevent repeated `_configure_group` calls
- **Status**: Should be fixed

## Files Modified
1. **`pythonScripts/bot/replay_manager.py`**: Fixed world record file path
2. **`pythonScripts/bot/chat_handler.py`**: Added debug prints for MAP command
3. **`pythonScripts/bot/utils.py`**: Added debug prints for world record lookup
4. **`pythonScripts/bot/tagpro_bot.py`**: Added group_configured flag and debug prints
5. **`pythonScripts/bot/requirements.txt`**: Added missing httpx and requests dependencies
6. **`docker-compose.yml`**: Added logs volume mapping

## Next Steps
1. Test MAP command in TagPro to see debug output
2. Verify world record lookup is working
3. Check why `current_game_preset` is None
4. Investigate volume mapping issue for logs

## Commands to Use
- View real-time logs: `docker-compose logs bot -f`
- Restart bot: `docker-compose restart bot`
- Rebuild and restart: `docker-compose up --build bot`

## Key Debug Points
- MAP command debug prints should show in Docker logs
- World record lookup debug prints should show file access
- Bot should only configure group once per session
