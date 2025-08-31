# TagPro Bot Deployment Guide

This guide explains how to deploy the refactored TagPro bot using different methods.

## Docker Deployment (Recommended)

The bot is designed to work seamlessly with the existing Docker setup.

### Files Updated for Docker

The following files have been updated to use the new refactored structure:

- `docker-compose.yml` - Updated to run `main.py` instead of `leader.py`
- `docker-compose.dev.yml` - Updated for development environment
- `Dockerfile.bot` - Updated CMD to use `main.py`

### Deploying with Docker

1. **Build and start all services:**
   ```bash
   docker-compose up -d
   ```

2. **View bot logs:**
   ```bash
   docker-compose logs -f bot
   ```

3. **Restart just the bot:**
   ```bash
   docker-compose restart bot
   ```

4. **Rebuild bot after code changes:**
   ```bash
   docker-compose build bot
   docker-compose up -d bot
   ```

### Docker File Structure

The Docker container mounts the bot directory as follows:
```
/app/bot/
├── main.py              # Entry point
├── tagpro_bot.py        # Main bot logic
├── driver_adapter.py    # WebDriver management
├── chat_handler.py      # Chat processing
├── settings_manager.py  # Configuration management
├── constants.py         # All constants and config
├── utils.py            # Utility functions
├── maps.py             # Map management (shared)
├── replay_manager.py   # Replay handling (shared)
└── requirements.txt    # Python dependencies
```

## Systemd Service Deployment

For deployment on a VM without Docker:

### Updated Files

- `tagpro-bot.service` - Updated to run `main.py`
- `setup_vm_github_actions.sh` - Updated process management

### Deploying with Systemd

1. **Copy files to VM:**
   ```bash
   scp -r pythonScripts/bot/ user@vm:/path/to/service/pythonScripts/
   ```

2. **Install service:**
   ```bash
   sudo cp tagpro-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable tagpro-bot
   sudo systemctl start tagpro-bot
   ```

3. **Check status:**
   ```bash
   sudo systemctl status tagpro-bot
   sudo journalctl -u tagpro-bot -f
   ```

## Local Development

### Prerequisites

1. **Activate virtual environment:**
   ```bash
   cd /Users/pierce/Projects/service
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   cd pythonScripts/bot
   pip install -r requirements.txt
   ```

### Running Locally

1. **Using the provided script:**
   ```bash
   ./run_bot.sh
   ```

2. **Manual activation:**
   ```bash
   cd /Users/pierce/Projects/service
   source venv/bin/activate
   cd pythonScripts/bot
   python main.py
   ```

## Migration from Old Structure

### What Changed

- **Old**: Single `leader.py` file with everything
- **New**: Modular structure with separate files for each responsibility

### Migration Steps

1. **Backup old file:**
   ```bash
   cp leader.py leader.py.backup
   ```

2. **Deploy new structure:**
   ```bash
   # Files are already in place from the refactoring
   ```

3. **Update Docker:**
   ```bash
   docker-compose build bot
   docker-compose up -d bot
   ```

4. **Verify functionality:**
   ```bash
   docker-compose logs -f bot
   ```

### Rollback (if needed)

If you need to rollback to the old structure:

1. **Restore old file:**
   ```bash
   cp leader.py.backup leader.py
   ```

2. **Update Docker files:**
   ```bash
   # Revert docker-compose.yml, docker-compose.dev.yml, Dockerfile.bot
   # Change command back to: python /app/bot/leader.py
   ```

3. **Rebuild and restart:**
   ```bash
   docker-compose build bot
   docker-compose up -d bot
   ```

## Configuration Management

### Settings Files

- **Bot settings**: `bot_settings.json` (auto-created)
- **Constants**: `constants.py` (hardcoded values)
- **Environment**: Docker environment variables

### Updating Configuration

1. **Bot settings** (category, difficulty, etc.):
   - Modified via chat commands: `SETTINGS category race`
   - Automatically saved to `bot_settings.json`

2. **Constants** (URLs, messages, etc.):
   - Edit `constants.py`
   - Rebuild Docker container: `docker-compose build bot`

3. **Environment variables**:
   - Edit `docker-compose.yml`
   - Restart: `docker-compose up -d bot`

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated or Docker container is built
2. **WebDriver issues**: Check Chrome/Chromium installation in container
3. **Settings not saving**: Check file permissions in mounted volumes

### Debug Commands

```bash
# Check bot logs
docker-compose logs -f bot

# Enter bot container
docker-compose exec bot bash

# Check file structure in container
docker-compose exec bot ls -la /app/bot/

# Test imports in container
docker-compose exec bot python /app/bot/test_imports.py
```

## Benefits of New Structure

1. **Easier maintenance**: Each file has a single responsibility
2. **Better testing**: Components can be tested independently
3. **Clearer code**: Logic is organized by function
4. **Easier debugging**: Issues can be isolated to specific components
5. **Better collaboration**: Multiple developers can work on different components
