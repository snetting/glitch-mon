#!/bin/bash
# run-client.sh - Run a client node using podman or docker

if command -v podman &> /dev/null; then
    echo "Using podman kube play..."
    # Attempt to use --replace for kube play (available in newer Podman)
    # If it fails, fallback to a manual down/play sequence
    if ! podman kube play --replace deploy/glitch-client-kube.yaml 2>/dev/null; then
        podman kube down deploy/glitch-client-kube.yaml 2>/dev/null || true
        podman kube play deploy/glitch-client-kube.yaml
    fi
elif command -v docker &> /dev/null; then
    echo "Podman not found, falling back to docker run..."
    SERVER_URL=${SERVER_URL:-"http://www.track3.org.uk:8002"}
    NTFY_TOPIC=${NTFY_TOPIC:-"steve_random_glitch"}
    docker rm -f glitch-client 2>/dev/null || true
    docker run -d \
      --name glitch-client \
      -e SERVER_URL="$SERVER_URL" \
      -e NTFY_TOPIC="$NTFY_TOPIC" \
      --restart unless-stopped \
      glitch-client:latest
else
    echo "Error: Neither podman nor docker found in PATH. Exiting."
    exit 1
fi

echo "Client deployment attempted."
