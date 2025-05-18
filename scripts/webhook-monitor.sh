#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_FILE="/var/log/webhook-deployments.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Monitor the webhook trigger file
log "Starting webhook monitor"
while true; do
    if [ -f "$PROJECT_DIR/data/webhook_trigger" ]; then
        log "Webhook triggered"
        cd "$PROJECT_DIR"
        
        # Get current commit hash before pull
        OLD_HASH=$(git rev-parse HEAD)
        log "Current commit: $OLD_HASH"

        # Pull latest changes
        if ! git pull; then
            log "Failed to pull latest changes"
            rm "$PROJECT_DIR/data/webhook_trigger"
            continue
        fi

        # Get new commit hash
        NEW_HASH=$(git rev-parse HEAD)
        log "New commit: $NEW_HASH"

        # If no changes, exit
        if [ "$OLD_HASH" = "$NEW_HASH" ]; then
            log "No changes detected, skipping deployment"
            rm "$PROJECT_DIR/data/webhook_trigger"
            continue
        fi

        # Stop containers
        log "Stopping containers"
        docker-compose down

        # Build and start new containers
        log "Building and starting new containers"
        if ! docker-compose up -d --build; then
            log "Failed to start containers"
            rm "$PROJECT_DIR/data/webhook_trigger"
            continue
        fi

        log "Deployment successful"
        rm "$PROJECT_DIR/data/webhook_trigger"
    fi
    sleep 1
done 