# Omni Link Husky Simulation

Lightweight Python simulator that runs a Clearpath Husky in a PyBullet physics world and exposes simple REST endpoints (Flask) for commanding the robot. Also includes small Omni Link bridge helpers under `robot_link/` to translate natural-language commands into REST calls.

---

## Features

- Realtime physics (PyBullet) at 240 Hz
- REST API (Flask) for commanding linear/angular velocity, stop, reset, and convenience motions
- Live pose telemetry exposed at `/pose`
- Simple obstacle-course entry point variant
- Omni Link bridge scripts (MQTT / TCP / remote poll + helpers) to translate Omni Link commands into simulator REST calls

---

## Project layout

.
- README.md — this file
- requirements.txt — Python dependencies (pip)
- husky_drive.py — main simulator + REST server
- husky_obstacle_course.py — alternate simulator with obstacles
- robot_link/ — Omni Link bridges and helpers
  - link_mqtt.py
  - link_tcp.py
  - link_remote.py
  - robot_api.py
  - omnilink.py (local OmniLink engine)
  - tcp_client.py
  - robot_commands.txt

Note: `omnilink` referenced in the bridge scripts is the local module `robot_link/omnilink.py` — not an external pip package.

---

## Prerequisites

- Python 3.9 or newer
- A system capable of running PyBullet GUI (X11 / Wayland). For headless servers use Xvfb (or run PyBullet in DIRECT mode by editing `setup_world()`).
- pip (Python package installer)

Optional (for headless servers):
- xvfb-run (package `xvfb` / `xvfb-run` on Debian/Ubuntu)
- system OpenGL libs (e.g., `libgl1-mesa-glx` / `mesa`)

---

## Dependencies (auto-extracted)

Standard library modules used (no install required):
- time, threading, typing, re, pathlib, os, json, socket, sys

External packages (install via pip):
- flask
- pybullet
- requests
- paho-mqtt

These are listed in `requirements.txt` included in this repository.

---

## Installation — step by step (explicit)

1. Open a terminal and execute the commands:
   ```bash
   git clone https://github.com/omni-link-tech/omni-link-husky-fleet.git
   cd omni-link-husky-fleet
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Upgrade pip (recommended):
   ```bash
   python -m pip install --upgrade pip
   ```

4. Install the Python dependencies from the included file:
   ```bash
   pip install -r requirements.txt
   ```

Optional: on headless CI / servers, install Xvfb and run the simulator under it:
   - Debian / Ubuntu:
     ```bash
     sudo apt update
     sudo apt install -y xvfb libgl1-mesa-glx
     xvfb-run python husky_drive.py
     ```
   - Or edit `setup_world()` in `husky_drive.py` to use `p.DIRECT` instead of `p.GUI` for headless runs.

---

## requirements.txt

A simple requirements file is provided at the repository root. It contains:
- flask
- pybullet
- requests
- paho-mqtt

(Install with `pip install -r requirements.txt` as shown above.)

---

## Usage

Start the simulator + REST server

- Standard run (shows PyBullet GUI):
  ```bash
  python husky_drive.py
  ```

- Obstacle-course variant:
  ```bash
  python husky_obstacle_course.py
  ```

After starting, the Flask server listens on http://127.0.0.1:5000 by default.

REST endpoints (examples)

- Health
  ```bash
  curl http://127.0.0.1:5000/health
  # => {"ok": true}
  ```

- Pose (latest telemetry)
  ```bash
  curl http://127.0.0.1:5000/pose
  # => {"x": 0.0, "y": 0.0, "yaw": 0.0}
  ```

- Drive (vx in m/s, wz in rad/s, optional duration in seconds)
  ```bash
  curl -X POST http://127.0.0.1:5000/drive \
    -H "Content-Type: application/json" \
    -d '{"vx": 0.6, "wz": 0.0, "duration": 2.0}'
  ```

- Stop
  ```bash
  curl -X POST http://127.0.0.1:5000/stop
  ```

- Reset
  ```bash
  curl -X POST http://127.0.0.1:5000/reset
  ```

- Convenience endpoints
  - Forward:
    ```bash
    curl -X POST http://127.0.0.1:5000/forward \
      -H "Content-Type: application/json" \
      -d '{"speed": 0.5, "duration": 1.0}'
    ```
  - Turn left:
    ```bash
    curl -X POST http://127.0.0.1:5000/turn_left \
      -H "Content-Type: application/json" \
      -d '{"rate": 1.2, "duration": 0.8}'
    ```

Omni Link bridges

- MQTT bridge (uses local `omnilink` engine + `robot_api` helpers)
  ```bash
  python robot_link/link_mqtt.py
  ```

- TCP / remote bridges:
  ```bash
  python robot_link/link_tcp.py
  python robot_link/link_remote.py
  ```

Note: the bridge scripts import and call the local `robot_link/robot_api.py` functions to issue HTTP calls to the running simulator. They require the same virtual environment as the simulator.

---

## Configuration / Environment Variables

- HUSKY_API_URL — (used by `robot_link/robot_api.py`) optional base URL for the simulator REST API. If unset the default `http://127.0.0.1:5000` is used. You can set it before starting the bridge scripts:

  ```bash
  export HUSKY_API_URL="http://192.168.1.10:5000"
  python robot_link/link_mqtt.py
  ```

- Flask host/port — change in `husky_drive.py` `app.run(...)` call as needed.

- Headless mode — edit `setup_world()` in `husky_drive.py` and set `p.connect(p.DIRECT)` in place of `p.connect(p.GUI)`.

---

# Demo Setup Guide

Follow these steps to run the OmniLink + Husky Simulator demo smoothly
on your machine.

## Step 1 --- Start the Husky Simulator (Flask API)

``` bash
python husky_fleet.py
```

Keep this terminal running and ensure the PyBullet GUI window opens.

## Step 2 --- Configure & Start the MQTT Broker (Mosquitto)

The OmniLink Agent requires MQTT over WebSockets on port 9001 with
anonymous access enabled.

### Stop Existing Mosquitto Service

``` bash
sudo systemctl stop mosquitto.service
```

### Edit Configuration

``` bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add the following:

    allow_anonymous true
    listener 9001
    protocol websockets

### Start Mosquitto

``` bash
sudo systemctl start mosquitto.service
```

## Step 3 --- Launch the OmniLink Bridge Script

### Set environment variables

``` bash
export HUSKY_API_URL=http://127.0.0.1:5000
export HUSKY_ROBOT_ID=husky_0
```

### Navigate to the bridge

``` bash
cd robot_link/
```

### Start the bridge

``` bash
python link_mqtt.py
```

Expected logs:

    [OmniLinkMQTT] Connected localhost:9001...
    Subscribed to olink/commands.

# OmniLink UI Configuration

## Connection Settings

-   **BROKER URL:** `ws://localhost:9001`
-   **Command Topic:** `olink/commands`

## Command Templates

Go to **Settings → Commands** and use the provided templates to avoid
parsing errors.

# Usage & Verification

Example command in the UI:

> Move forward at 0.5 m/s for 3 seconds.

### Expected behavior:

-   Bridge logs the parsed command.
-   Simulator may log an HTTP POST.
-   PyBullet robot moves for 3 seconds and stops.

## Troubleshooting & Notes

- No GUI appears
  - Ensure a display is available. On headless machines use `xvfb-run` or run PyBullet in DIRECT mode.
  - Install system OpenGL libraries if you see rendering errors (e.g., `libgl1-mesa-glx`).

- Robot does not move
  - Commands must be numeric values (JSON numbers, not strings).
  - Commands are clamped to `MAX_VX` and `MAX_WZ` defined in `husky_drive.py`.
  - If using the bridges, ensure `HUSKY_API_URL` points to the running simulator.

- Reset endpoint caveat (known issue)
  - The `/reset` endpoint in the distributed sample manipulates the PyBullet world from the Flask thread. PyBullet's API is not thread-safe and a safer approach is to post a reset request that the physics thread consumes. If you see crashes when calling `/reset` while the simulator is running, consider modifying `api_reset()` to signal the physics loop rather than directly calling PyBullet APIs from the Flask thread.

- Mixed natural-language parsing
  - Bridge scripts parse numeric arguments from free-form command strings. Commands mixing words and numbers (e.g., "two seconds") may not parse correctly. Use numeric values or adapt the bridge code to use structured `vars` from the OmniLink engine.

- Graceful shutdown
  - Long-running scripts currently do not implement SIGINT/SIGTERM-based graceful shutdown. Stopping them via Ctrl+C will kill the process; consider adding signal handlers to stop loops and close connections cleanly for production use.

---

## License

No license file is included in this repository. If you want to redistribute or reuse this code, add a LICENSE file (for example MIT) or consult the repository owner.

---

