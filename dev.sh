#!/bin/bash

# TagPro Services Development Script
# This script runs both services locally for development

set -e

echo "🔧 Starting TagPro Services in development mode..."

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

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose down

# Build services
echo "🔨 Building services..."
docker-compose build

# Start services in foreground for development
echo "🚀 Starting services in development mode..."
echo "Press Ctrl+C to stop all services"
docker-compose up
