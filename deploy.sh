#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${YELLOW}[*] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

print_error() {
    echo -e "${RED}[-] $1${NC}"
}

# Function to check if a command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        print_success "$1"
    else
        print_error "$2"
        exit 1
    fi
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Get the username of the user who ran sudo
ACTUAL_USER=$(logname)
if [ -z "$ACTUAL_USER" ]; then
    ACTUAL_USER=$SUDO_USER
fi

print_status "Starting server setup for user: $ACTUAL_USER"

# System Updates
print_status "Updating system packages..."
apt-get update
check_status "System packages updated" "Failed to update system packages"

apt-get upgrade -y
check_status "System upgraded" "Failed to upgrade system"

# Install required packages
print_status "Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    git
check_status "Required packages installed" "Failed to install required packages"

# Install Docker
print_status "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
check_status "Docker installed" "Failed to install Docker"

# Install Docker Compose
print_status "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
check_status "Docker Compose installed" "Failed to install Docker Compose"

# Add user to docker group
print_status "Adding user to docker group..."
usermod -aG docker $ACTUAL_USER
check_status "User added to docker group" "Failed to add user to docker group"

# Create backup directory
print_status "Setting up backup directory..."
mkdir -p /backup
chown $ACTUAL_USER:$ACTUAL_USER /backup
check_status "Backup directory created" "Failed to create backup directory"

# Create scripts directory
print_status "Creating scripts directory..."
mkdir -p scripts
check_status "Scripts directory created" "Failed to create scripts directory"

# Make scripts executable and set proper ownership
print_status "Setting up script permissions..."
chown -R $ACTUAL_USER:$ACTUAL_USER scripts/
chmod -R 755 scripts/
check_status "Script permissions set" "Failed to set script permissions"

# Create symlinks
print_status "Creating symlinks..."
ln -sf "$(pwd)/scripts/webhook-handler.sh" /usr/local/bin/webhook-handler
ln -sf "$(pwd)/scripts/backup.sh" /usr/local/bin/backup
check_status "Symlinks created" "Failed to create symlinks"

# Create log file and set permissions
print_status "Setting up deployment log file..."
touch /var/log/webhook-deployments.log
chown $ACTUAL_USER:$ACTUAL_USER /var/log/webhook-deployments.log
chmod 644 /var/log/webhook-deployments.log
check_status "Log file created" "Failed to create log file"

# Set up cron job for backups
print_status "Setting up backup cron job..."
(crontab -u $ACTUAL_USER -l 2>/dev/null; echo "0 0 * * * /usr/local/bin/backup") | crontab -u $ACTUAL_USER -
check_status "Backup cron job created" "Failed to create backup cron job"

# Install Certbot
print_status "Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx
check_status "Certbot installed" "Failed to install Certbot"

# Create required directories
print_status "Creating required directories..."
mkdir -p nginx/conf.d nginx/ssl nginx/www
check_status "Directories created" "Failed to create directories"

# Create Nginx configuration
print_status "Creating Nginx configuration..."
cat > nginx/conf.d/default.conf << 'NGINX'
server {
    listen 80;
    server_name _;  # This will match any domain

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
check_status "Nginx configuration created" "Failed to create Nginx configuration"

# Build and start containers
print_status "Building and starting containers..."
docker-compose up -d --build
check_status "Containers started" "Failed to start containers"

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

print_success "Deployment completed!"
print_status "Your application is now accessible at:"
echo "- http://$SERVER_IP"
print_status "To set up SSL with a domain name:"
echo "1. Point your domain to this IP: $SERVER_IP"
echo "2. Run: sudo certbot certonly --standalone -d your-domain.com"
echo "3. Update nginx/conf.d/default.conf with your domain name"
echo "4. Restart the containers: docker-compose restart"

print_status "IMPORTANT: Please log out and log back in for Docker group changes to take effect" 