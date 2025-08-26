#!/bin/bash

# TagPro HTTPS Setup Script
# This script sets up HTTPS with self-signed certificates

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Setting up HTTPS for TagPro...${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script with sudo${NC}"
    exit 1
fi

# Install SSL tools if not present
if ! command -v openssl &> /dev/null; then
    echo -e "${YELLOW}Installing OpenSSL...${NC}"
    apt-get update
    apt-get install -y openssl
fi

# Create SSL directory
mkdir -p /etc/ssl/private
mkdir -p /etc/ssl/certs

# Generate self-signed certificate
echo -e "${YELLOW}Generating self-signed SSL certificate...${NC}"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/ssl-cert-snakeoil.key \
    -out /etc/ssl/certs/ssl-cert-snakeoil.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set proper permissions
chmod 600 /etc/ssl/private/ssl-cert-snakeoil.key
chmod 644 /etc/ssl/certs/ssl-cert-snakeoil.pem

# Copy HTTPS nginx config
echo -e "${YELLOW}Updating nginx configuration...${NC}"
if [ -f "nginx/conf.d/default-https.conf" ]; then
    cp nginx/conf.d/default-https.conf /etc/nginx/conf.d/
    rm /etc/nginx/conf.d/default.conf 2>/dev/null || true
else
    echo -e "${RED}HTTPS nginx config not found!${NC}"
    exit 1
fi

# Test nginx configuration
echo -e "${YELLOW}Testing nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}Nginx configuration is valid${NC}"
else
    echo -e "${RED}Nginx configuration is invalid${NC}"
    exit 1
fi

# Restart nginx
echo -e "${YELLOW}Restarting nginx...${NC}"
systemctl restart nginx

echo -e "${GREEN}HTTPS setup complete!${NC}"
echo -e "${YELLOW}Your site is now available at:${NC}"
echo -e "  • https://localhost (HTTPS)"
echo -e "  • http://localhost (redirects to HTTPS)"
echo ""
echo -e "${YELLOW}Note: You'll see a browser warning about the self-signed certificate.${NC}"
echo -e "${YELLOW}This is normal for development. For production, use Let's Encrypt.${NC}"
