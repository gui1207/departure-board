#!/bin/bash

# Configuration
PI_USER="pi"
PI_HOST="raspberrypi.local"
LOCAL_PATH="./"
REMOTE_PATH="/home/pi/departure-board"

# Sync command
rsync -avz \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude 'venv/' \
    "$LOCAL_PATH" "$PI_USER@$PI_HOST:$REMOTE_PATH"


echo "Sync complete!"