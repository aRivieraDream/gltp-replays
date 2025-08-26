#!/bin/bash

# TagPro VM Setup Script for GitHub Actions
# This script sets up your VM for automatic deployment via GitHub Actions

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== TagPro VM Setup for GitHub Actions ===${NC}"
echo "This script will set up your VM for automatic deployment via GitHub Actions"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Update system packages
echo -e "${YELLOW}Updating system packages...${NC}"
apt-get update && apt-get upgrade -y

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
apt-get install -y \
    curl \
    git \
    htop \
    unzip \
    wget

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${GREEN}Docker is already installed${NC}"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}Docker Compose is already installed${NC}"
fi

# Create log directory
echo -e "${YELLOW}Setting up logging...${NC}"
mkdir -p /var/log
touch /var/log/tagpro-deployments.log

# Set up log rotation
cat > /etc/logrotate.d/tagpro << EOF
/var/log/tagpro-deployments.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

# Make scripts executable
echo -e "${YELLOW}Setting up scripts...${NC}"
chmod +x scripts/*.sh

# Set up systemd service
echo -e "${YELLOW}Setting up systemd service...${NC}"

# Copy service file to systemd directory
cp tagpro.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service
echo -e "${YELLOW}Enabling service...${NC}"
systemctl enable tagpro.service

# Set up firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    echo -e "${YELLOW}Setting up firewall...${NC}"
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw --force enable
    echo -e "${GREEN}Firewall configured${NC}"
fi

# Create SSH key for GitHub Actions
echo -e "${YELLOW}Setting up SSH for GitHub Actions...${NC}"
if [ ! -f /root/.ssh/id_rsa ]; then
    echo -e "${YELLOW}Generating SSH key pair...${NC}"
    ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
    echo -e "${GREEN}SSH key generated${NC}"
else
    echo -e "${GREEN}SSH key already exists${NC}"
fi

# Display public key
echo ""
echo -e "${GREEN}=== SSH Public Key for GitHub Actions ===${NC}"
echo "Copy this public key and add it to your GitHub repository secrets as VM_SSH_KEY:"
echo ""
cat /root/.ssh/id_rsa.pub
echo ""

# Create a simple status check script
echo -e "${YELLOW}Creating status check script...${NC}"
cat > /usr/local/bin/tagpro-status << 'EOF'
#!/bin/bash
echo "=== TagPro Services Status ==="
echo ""
echo "Docker containers:"
docker-compose ps
echo ""
echo "Systemd service:"
systemctl status tagpro.service --no-pager -l
echo ""
echo "Recent deployment logs:"
tail -10 /var/log/tagpro-deployments.log
EOF

chmod +x /usr/local/bin/tagpro-status

# Create a simple restart script
echo -e "${YELLOW}Creating restart script...${NC}"
cat > /usr/local/bin/tagpro-restart << 'EOF'
#!/bin/bash
cd /root/service
docker-compose down
docker-compose up -d --build
echo "Services restarted"
EOF

chmod +x /usr/local/bin/tagpro-restart

# Final setup
echo ""
echo -e "${GREEN}=== VM Setup Complete! ===${NC}"
echo ""
echo -e "${YELLOW}What's been set up:${NC}"
echo "• System packages updated"
echo "• Docker and Docker Compose installed"
echo "• Logging configured with rotation"
echo "• Systemd service enabled"
echo "• Firewall configured (if available)"
echo "• SSH key generated for GitHub Actions"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Add the SSH public key above to your GitHub repository secrets as VM_SSH_KEY"
echo "2. Add these secrets to your GitHub repository:"
echo "   - VM_SSH_KEY: The private key content from /root/.ssh/id_rsa"
echo "   - VM_HOST: Your VM's IP address or hostname"
echo "   - VM_USER: root (or your preferred user)"
echo "3. Start your service: systemctl start tagpro.service"
echo "4. Push to main branch to trigger automatic deployment"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "• tagpro-status          - Check service status"
echo "• tagpro-restart         - Restart all services"
echo "• docker-compose logs -f - View live logs"
echo ""
echo -e "${GREEN}Your VM is now ready for GitHub Actions deployment!${NC}"
