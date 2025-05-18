#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_FILE="/var/log/webhook-deployments.log"
MAX_RETRIES=3
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_INTERVAL=5

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

check_health() {
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s -f http://localhost/ > /dev/null; then
            return 0
        fi
        retries=$((retries + 1))
        sleep $HEALTH_CHECK_INTERVAL
    done
    return 1
}

rollback() {
    log "Starting rollback to previous version"
    git reset --hard HEAD^
    docker-compose down
    docker-compose up -d --build
    
    if check_health; then
        log "Rollback successful"
        return 0
    else
        log "Rollback failed - manual intervention required"
        return 1
    fi
}

# Start deployment
log "Starting deployment"
cd $(dirname "$0")/..

# Get current commit hash before pull
OLD_HASH=$(git rev-parse HEAD)
log "Current commit: $OLD_HASH"

# Pull latest changes
if ! git pull; then
    log "Failed to pull latest changes"
    exit 1
fi

# Get new commit hash
NEW_HASH=$(git rev-parse HEAD)
log "New commit: $NEW_HASH"

# If no changes, exit
if [ "$OLD_HASH" = "$NEW_HASH" ]; then
    log "No changes detected, skipping deployment"
    exit 0
fi

# Stop containers
log "Stopping containers"
docker-compose down

# Build and start new containers
log "Building and starting new containers"
if ! docker-compose up -d --build; then
    log "Failed to start containers"
    rollback
    exit 1
fi

# Wait for containers to be ready
log "Waiting for health check"
sleep 5

# Check if the application is healthy
if ! check_health; then
    log "Health check failed after deployment"
    rollback
    exit 1
fi

log "Deployment successful" 