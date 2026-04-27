#!/bin/bash
# run-client-docker.sh - Run a client node (works with podman or docker)

if command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
elif command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
else
    echo "Error: Neither podman nor docker found in PATH. Exiting."
    exit 1
fi

SERVER_URL=${SERVER_URL:-"http://www.track3.org.uk:8002"}
NTFY_TOPIC=${NTFY_TOPIC:-"steve_random_glitch"}

$DOCKER_CMD rm -f glitch-client 2>/dev/null || true

echo "Using $DOCKER_CMD for client..."
echo "Starting Client connected to $SERVER_URL..."
$DOCKER_CMD run -d \
  --name glitch-client \
  -e SERVER_URL="$SERVER_URL" \
  -e NTFY_TOPIC="$NTFY_TOPIC" \
  --restart unless-stopped \
  glitch-client:latest

echo "Client running in background."
