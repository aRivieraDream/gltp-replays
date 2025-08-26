# TagPro Services

This project contains two main services that work together to manage TagPro games and provide a leaderboard website:

1. **Bot Service** - A Discord bot that manages TagPro games and launches matches
2. **Web Service** - A FastAPI application that serves the leaderboard website and handles webhooks

Both services run as separate Docker containers on the same VM, sharing data through mounted volumes.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy  │    │   Web Service   │    │   Bot Service   │
│   (Ports 80/443)│◄──►│   (Port 8000)   │    │   (Background)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Shared Data   │
                    │   (./data/)     │
                    └─────────────────┘
```

## Services

### Web Service (`web`)
- **Purpose**: Serves the leaderboard website and handles GitHub webhooks
- **Port**: 8000 (internal)
- **Dependencies**: FastAPI, Uvicorn, Selenium, RapidFuzz
- **Features**: 
  - Static file serving
  - Replay processing
  - Webhook handling
  - Map management

### Bot Service (`bot`)
- **Purpose**: Manages TagPro games via Discord
- **Dependencies**: Discord.py, Selenium, Chrome
- **Features**:
  - Discord bot functionality
  - Game launching
  - Selenium automation

### Nginx (`nginx`)
- **Purpose**: Reverse proxy and SSL termination
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Features**: 
  - Routes traffic to web service
  - SSL certificate management
  - Static file caching

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git repository cloned

### Development Mode
```bash
# Start services in foreground (good for development)
./dev.sh
```

### Production Deployment
```bash
# Deploy to production
./deploy.sh
```

### Manual Control
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web      # Web service logs
docker-compose logs -f bot      # Bot service logs
docker-compose logs -f nginx    # Nginx logs

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart web
docker-compose restart bot
```

## Data Sharing

Both services share data through the `./data/` directory:
- `replays/` - Processed replay files
- `replay_stats.json` - Replay statistics
- `replay_uris.json` - Replay URIs
- `unprocessed_replays.json` - Queue of replays to process

## Configuration

### Environment Variables
- `PYTHONUNBUFFERED=1` - Ensures Python output is not buffered
- `PYTHONDONTWRITEBYTECODE=1` - Prevents Python from writing .pyc files

### Volumes
- `./data:/app/data` - Shared data directory
- `./nginx/conf.d:/etc/nginx/conf.d` - Nginx configuration
- `./nginx/ssl:/etc/nginx/ssl` - SSL certificates
- `./nginx/www:/var/www/html` - Static web files

## Systemd Service

For production deployment, you can use the provided systemd service:

```bash
# Copy service file
sudo cp tagpro.service /etc/systemd/system/

# Enable and start
sudo systemctl enable tagpro
sudo systemctl start tagpro

# Check status
sudo systemctl status tagpro
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 80 and 443 are available
2. **Permission issues**: Check that the `./data/` directory is writable
3. **Chrome/Selenium issues**: The bot container includes Chrome for Selenium automation

### Logs
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f web
docker-compose logs -f bot

# View last 50 lines
docker-compose logs --tail=50
```

### Service Health
```bash
# Check service status
docker-compose ps

# Check service health
docker-compose exec web curl -f http://localhost:8000/ || echo "Web service down"
docker-compose exec bot python -c "import discord; print('Bot dependencies OK')" || echo "Bot service down"
```

## Development

### Adding New Features
1. **Web Service**: Add endpoints to `main.py`
2. **Bot Service**: Modify `pythonScripts/bot/leader.py`
3. **Shared Logic**: Place in root-level Python files (e.g., `maps.py`, `jsonutil.py`)

### Testing Changes
```bash
# Rebuild and restart specific service
docker-compose build web
docker-compose restart web

# Or rebuild and restart all
docker-compose build
docker-compose restart
```

## Security Notes

- The web service exposes port 8000 internally only
- Nginx handles external traffic and SSL termination
- Bot service runs in background with no external ports
- Data directory is shared between services - ensure proper permissions
