# Glitch Monitor (GlitchWatch)

*"The universe is basically data."*

## Inspiration

Glitch Monitor is an experimental, distributed system designed to monitor local hardware entropy for statistical anomalies. 

The philosophical drive behind this project stems from the current revelations and hypotheses that **everything is connected**, suggesting that the universe at its fundamental level is informational—basically data. If this is true, then local, isolated random number generators (hardware entropy sources) might be susceptible to broader, non-local influences. 

Furthermore, if **intent is powerful** and consciousness interacts with the physical world, localized spikes in anomalous random behavior might correlate with significant events, shifts in collective consciousness, or focused intent. This concept is partly inspired by the work and interviews of **Nick Cook** from the [Exo Institute](https://www.exoinstitute.io/), particularly his discussions featured on *That UFO Podcast*. 

Whether the random source is cryptographic, quantum, or atmospheric, it doesn't matter if you operate under the paradigm that the underlying data structure of reality is interconnected.

## Architecture

The project is split into three main components:

1. **Central Server (`/server`)**: A FastAPI application that aggregates anomaly reports from distributed clients, provides a web dashboard for visualization, and serves the mobile PWA. It uses SQLite for persistence.
2. **Distributed Clients (`/client`)**: Python agents that continuously generate local randomness, run statistical tests (Monobit/Bias and Runs/Pattern) over a rolling window, and report significant deviations (p < 0.01) to the central server.
3. **Mobile Node / PWA**: A mobile-friendly web application served by the central server (`/static/mobile.html`). It utilizes the mobile browser's cryptographic randomness to act as a standalone, pocket-sized node, complete with a visual readout and notification capabilities.

## Getting Started

### Prerequisites
* **Docker** (for building and running the server/client)
* **Podman** (optional, for deploying the client via Kubernetes YAML)

### Building the Images
A unified build script is provided to compile both the server and client Docker images.

```bash
./build.sh
```

### Running the Server
The server runs via Docker. By default, it exposes port `8002` (which can be overridden via the `SERVER_PORT` environment variable).

```bash
./run-server.sh
```
*   **Web Dashboard:** `http://localhost:8002/`
*   **Mobile PWA Node:** `http://localhost:8002/static/mobile.html`

### Running a Client Node

You can run the client node using either Docker or Podman. Ensure the `SERVER_URL` points to your central server instance.

**Using Docker:**
```bash
# Set your server URL if different
export SERVER_URL="http://www.track3.org.uk:8002"
export NTFY_TOPIC="your_personal_topic" # Optional
./run-client-docker.sh
```

**Using Podman (Kube Play):**
Edit `deploy/glitch-client-kube.yaml` to point to your specific `SERVER_URL`, then run:
```bash
./run-client-podman.sh
```

## Contributing
Deploy nodes, watch the data, and keep an eye out for the glitches in the matrix.
