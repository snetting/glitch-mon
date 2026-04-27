#!/bin/bash
# run-server.sh - Run the server using podman or docker

if command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
elif command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
else
    echo "Error: Neither podman nor docker found in PATH. Exiting."
    exit 1
fi

PORT=${SERVER_PORT:-8002}

# Stop and remove existing container if it exists
$DOCKER_CMD rm -f glitch-server 2>/dev/null || true

# Ensure the DB file exists before mounting to avoid Docker creating a directory
touch ./server/anomalies.db

# Mapping Host Port (default 8002) to Container Port (8000)
echo "Using $DOCKER_CMD for server..."
echo "Starting Server on port $PORT..."
$DOCKER_CMD run -d \
  --name glitch-server \
  -p $PORT:8000 \
  -v "$(pwd)/server/anomalies.db:/app/anomalies.db" \
  --restart unless-stopped \
  glitch-server:latest

echo "Server running. Access dashboard at http://localhost:$PORT"
echo "Mobile/PWA accessible at http://localhost:$PORT/static/mobile.html"
