#!/bin/bash
# build.sh - Build both server and client images using podman or docker

if command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
elif command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
else
    echo "Error: Neither podman nor docker found in PATH. Exiting."
    exit 1
fi

echo "Using $DOCKER_CMD for builds..."

echo "Building Server Image (glitch-server:latest)..."
$DOCKER_CMD build -t glitch-server:latest ./server

echo ""
echo "Building Client Image (glitch-client:latest)..."
$DOCKER_CMD build -t glitch-client:latest ./client

echo ""
echo "Builds complete."
