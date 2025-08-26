# TagPro Service Management Commands

## Local Development
```bash
# Start services locally
./dev.sh

# Or manually with docker-compose
docker-compose up -d
docker-compose down
```

## Service Management
```bash
# Rebuild and restart the bot service
docker-compose build bot
docker-compose restart bot

# Or restart everything
docker-compose down
docker-compose up -d

# Check status of all containers:
docker-compose ps

# Get live messages from container
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f bot      # Bot service logs
docker-compose logs -f web      # Web service logs
docker-compose logs -f nginx    # Nginx logs
```

## VM Setup and Deployment
```bash
# Set up VM for GitHub Actions deployment
sudo ./setup_vm_github_actions.sh

# Manual deployment (if needed)
./scripts/auto-deploy.sh

# Check deployment status
tagpro-status

# Restart all services
tagpro-restart
```

## Systemd Services (VM)
```bash
# Start services
sudo systemctl start tagpro.service

# Check status
sudo systemctl status tagpro.service

# Enable auto-start
sudo systemctl enable tagpro.service
```

## GitHub Actions Deployment
The VM is automatically deployed when you push to the `main` branch. The workflow:

1. **Triggers**: Push to main branch or manual workflow dispatch
2. **SSH to VM**: Uses stored SSH key for secure access
3. **Pull Updates**: Fetches latest code from GitHub
4. **Rebuild Services**: Stops containers, rebuilds, and restarts
5. **Health Check**: Verifies deployment success
6. **Rollback**: Automatically rolls back if health check fails

## Monitoring and Logs
```bash
# View deployment logs
tail -f /var/log/tagpro-deployments.log

# Check GitHub Actions status
# Go to your repository → Actions tab

# View all running containers
docker ps -a
```

## Troubleshooting
```bash
# Check if Docker is running
docker info

# Check container health
curl -f http://localhost/

# View all running containers
docker ps -a

# Clean up Docker
docker system prune -f

# Check GitHub Actions secrets
# Go to repository → Settings → Secrets and variables → Actions
```
