#!/bin/bash
# run-client-podman.sh - Run a client node using Podman kube play

echo "Deploying client using Podman kube play..."
podman kube play deploy/glitch-client-kube.yaml

echo "Client deployed."
