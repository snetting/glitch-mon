#!/bin/bash
# run-server.sh - Run the server using Docker

PORT=${SERVER_PORT:-8002}

# Stop and remove existing container if it exists
docker rm -f glitch-server 2>/dev/null || true

# Ensure the DB file exists before mounting to avoid Docker creating a directory
touch ./server/anomalies.db

# Mapping Host Port (default 8002) to Container Port (8000)
echo "Starting Server on port $PORT..."
docker run -d \
  --name glitch-server \
  -p $PORT:8000 \
  -v "$(pwd)/server/anomalies.db:/app/anomalies.db" \
  --restart unless-stopped \
  glitch-server:latest

echo "Server running. Access dashboard at http://localhost:$PORT"
echo "Mobile/PWA accessible at http://localhost:$PORT/static/mobile.html"
