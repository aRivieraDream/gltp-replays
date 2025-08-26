#!/bin/bash

# TagPro Services Deployment Script
# This script deploys both the bot and web services

set -e

echo "🚀 Deploying TagPro Services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

# Check logs
echo "📝 Recent logs:"
docker-compose logs --tail=20

echo "✅ Deployment complete!"
echo ""
echo "Services running:"
echo "  🌐 Web Service: http://localhost (via Nginx)"
echo "  🤖 Bot Service: Running in background"
echo "  🔄 Nginx: Reverse proxy on ports 80/443"
echo ""
echo "To view logs: docker-compose logs -f [service_name]"
echo "To stop: docker-compose down"
echo "To restart: docker-compose restart [service_name]" 