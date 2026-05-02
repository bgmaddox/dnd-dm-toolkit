#!/bin/bash
# Sync DnD toolkit to Pi and restart the service.
# Run from your Mac: ./deploy_pi.sh

set -e

PI="bgmaddox@rachett.local"
REMOTE_DIR="/home/bgmaddox/dnd"

echo "Syncing files to Pi..."
rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.git' --exclude='.env' \
  /Users/brettmaddox/Documents/CODING/DnD/ \
  "$PI:$REMOTE_DIR/"

echo "Restarting service..."
ssh "$PI" "sudo systemctl restart dnd-toolkit"

echo "Done. Tools available at:"
echo "  http://rachett.local:8502/tools/npc_forge.html"
echo "  http://rachett.local:8502/tools/combat_companion.html"
