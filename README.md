# Glitch Monitor (GlitchWatch)

*"The universe is basically data."*

## Inspiration

Glitch Monitor is an experimental, distributed system designed to monitor local hardware entropy for statistical anomalies.

The philosophical drive behind this project stems from the current revelations and hypotheses that **everything is connected**, suggesting that the universe at its fundamental level is informational—basically data. If this is true, then local, isolated random number generators (hardware entropy sources) might be susceptible to broader, non-local influences. 

Furthermore, if **intent is powerful** and consciousness interacts with the physical world, localized spikes in anomalous random behavior might correlate with significant events, shifts in collective consciousness, or focused intent. This concept is partly inspired by the [Global Consciousness Project](https://en.wikipedia.org/wiki/Global_Consciousness_Project), and by the work and interviews of **Nick Cook** from the [Exo Institute](https://www.exoinstitute.io/), particularly his discussions featured on *That UFO Podcast*.

Whether the random source is cryptographic, quantum, or atmospheric, it doesn't matter if you operate under the paradigm that the underlying data structure of reality is interconnected.

## Architecture

The project is split into three main components:

1. **Central Server (`/server`)**: A FastAPI application that aggregates anomaly reports from distributed clients, provides a web dashboard for visualization, and serves the mobile PWA. It uses SQLite for persistence.
2. **Distributed Clients (`/client`)**: Python agents that continuously generate local randomness, run statistical tests (Monobit/Bias and Runs/Pattern) over a rolling window, scan anomaly buffers for leaked words, and report significant deviations to the central server.
3. **Mobile Node / PWA**: A mobile-friendly web application served by the central server (`/static/mobile.html`). It utilizes the mobile browser's cryptographic randomness to act as a standalone, pocket-sized node, complete with a visual readout and notification capabilities.

## Dashboard

The server dashboard shows active reporters, recent anomalies, a map, a correlation chart, and any leaked words reported by clients. A shared time selector drives the map, anomaly list, chart, and leaked-word panel together. Supported views are 15 minutes, 1 hour, 24 hours, week, month, all time, and a custom event lookup for a day/week/month around a selected date.

Leaked words are dictionary matches found only after a statistical glitch triggers an intensive scan of the same rolling bit buffer. The Python client scans ASCII across bit shifts, inverted bytes, bit-reversed bytes, and backwards byte order, reporting dictionary words of 4 or more letters.

## Alert Rate

Both the Python client and mobile PWA use a 10,000-bit rolling window, analyze once per minute, and alert when either statistical test returns `p < 3e-3`. Because adjacent analyses mostly reuse the same rolling-window data, this targets roughly one false-positive-style "glitch" every 2-3 days per continuously running client. The Python client can override this with `GLITCH_P_THRESHOLD`, `GLITCH_WINDOW_SIZE`, and `GLITCH_ANALYSIS_INTERVAL`.

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

**Using the helper script:**
```bash
# Set your server URL if different
export SERVER_URL="http://www.track3.org.uk:8002"
export NTFY_TOPIC="your_personal_topic" # Optional
./run-client.sh
```

If Podman is installed, `run-client.sh` uses `podman kube play` with `deploy/glitch-client-kube.yaml`. If Docker is installed instead, it falls back to `docker run`.

**Using Podman directly:**
Edit `deploy/glitch-client-kube.yaml` to point to your specific `SERVER_URL` and notification topic, then run:
```bash
podman kube play --replace deploy/glitch-client-kube.yaml
```

## Contributing
Deploy nodes, watch the data, and keep an eye out for the glitches in the matrix.
