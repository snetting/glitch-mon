#!/bin/bash
# run-client-docker.sh - Run a client node using Docker

# Default configurations, can be overridden by exporting environment variables
SERVER_URL=${SERVER_URL:-"http://www.track3.org.uk:8002"}
NTFY_TOPIC=${NTFY_TOPIC:-"steve_random_glitch"}

docker rm -f glitch-client 2>/dev/null || true

echo "Starting Client connected to $SERVER_URL..."
docker run -d \
  --name glitch-client \
  -e SERVER_URL="$SERVER_URL" \
  -e NTFY_TOPIC="$NTFY_TOPIC" \
  --restart unless-stopped \
  glitch-client:latest

echo "Client running in background."
