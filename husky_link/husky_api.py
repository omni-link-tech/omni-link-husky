"""HTTP client for the Husky robot simulator."""

from __future__ import annotations

import json
from typing import Any

import requests

SERVER_URL = "http://127.0.0.1:5000"

# Reuse a persistent session for connection pooling.
_session = requests.Session()


def get_state() -> dict[str, Any]:
    """Fetch the current robot state from the simulator.

    Returns the parsed state dict with keys: x, y, yaw.
    """
    r = _session.get(f"{SERVER_URL}/pose", timeout=2)
    return r.json()


def send_action(action: str, **kwargs: Any) -> None:
    """Send a single action to the robot.

    Supported actions: FORWARD, BACKWARD, LEFT, RIGHT, STOP, RESET, DRIVE.
    Extra keyword arguments (speed, rate, duration, vx, wz) are passed as JSON.
    """
    action = action.upper()
    endpoint_map = {
        "FORWARD": "/forward",
        "BACKWARD": "/backward",
        "LEFT": "/turn_left",
        "RIGHT": "/turn_right",
        "STOP": "/stop",
        "RESET": "/reset",
    }

    if action == "DRIVE":
        _session.post(f"{SERVER_URL}/drive", json=kwargs, timeout=2)
    elif action in endpoint_map:
        _session.post(f"{SERVER_URL}{endpoint_map[action]}", json=kwargs, timeout=2)
    else:
        raise ValueError(f"Unknown action: {action}")


def drive(vx: float, wz: float, duration: float | None = None) -> None:
    """Send a raw drive command with linear and angular velocity."""
    payload: dict[str, Any] = {"vx": vx, "wz": wz}
    if duration is not None:
        payload["duration"] = duration
    _session.post(f"{SERVER_URL}/drive", json=payload, timeout=2)
