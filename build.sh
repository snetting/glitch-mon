#!/bin/bash
# build.sh - Build both server and client Docker images

echo "Building Server Image (glitch-server:latest)..."
docker build -t glitch-server:latest ./server

echo ""
echo "Building Client Image (glitch-client:latest)..."
docker build -t glitch-client:latest ./client

echo ""
echo "Builds complete."
