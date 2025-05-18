#!/bin/bash
timestamp=$(date +%Y%m%d_%H%M%S)
tar -czf /backup/replay-data-$timestamp.tar.gz $(dirname "$0")/../data 