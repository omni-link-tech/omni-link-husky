"""Local Husky AI engine — waypoint navigation controller.

This module is the ``make_move`` tool: given the current robot pose and a
list of waypoints, it computes the steering command (linear + angular
velocity) to drive toward the next waypoint.

The controller uses a pure-pursuit-style approach:
  1. Compute bearing to next waypoint.
  2. Compute heading error (difference between current yaw and bearing).
  3. Proportional angular velocity to correct heading.
  4. Reduce linear speed when heading error is large (turn first, then go).
  5. Mark waypoint as reached when within distance threshold.
"""

from __future__ import annotations

import math
from typing import Any

# Navigation constants.
WAYPOINT_REACH_DIST = 0.3    # metres — waypoint is "reached" within this radius.
MAX_VX = 0.8                 # m/s — cruise speed.
MIN_VX = 0.1                 # m/s — minimum forward creep while turning.
MAX_WZ = 1.5                 # rad/s — max angular velocity.
KP_ANGULAR = 2.0             # proportional gain for heading correction.
HEADING_SLOW_THRESH = 0.4    # rad — start reducing speed when error exceeds this.

# Default waypoint circuit.
DEFAULT_WAYPOINTS: list[tuple[float, float]] = [
    (2.0, 0.0),
    (2.0, 2.0),
    (0.0, 2.0),
    (0.0, 0.0),
]


def _normalise_angle(a: float) -> float:
    """Wrap angle to [-pi, pi]."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


class HuskyNavigator:
    """Stateful waypoint navigator for the Husky robot."""

    def __init__(self, waypoints: list[tuple[float, float]] | None = None,
                 loop: bool = True) -> None:
        self.waypoints = list(waypoints or DEFAULT_WAYPOINTS)
        self.loop = loop
        self.current_wp = 0
        self.laps = 0
        self.total_waypoints_reached = 0
        self.started = False

    @property
    def finished(self) -> bool:
        """True when all waypoints have been visited (non-loop mode only)."""
        if self.loop:
            return False
        return self.current_wp >= len(self.waypoints)

    @property
    def target(self) -> tuple[float, float] | None:
        """Return the current target waypoint, or None if finished."""
        if self.current_wp >= len(self.waypoints):
            return None
        return self.waypoints[self.current_wp]

    def decide_action(self, state: dict[str, Any]) -> dict[str, Any]:
        """Decide the drive command based on the current robot pose.

        Parameters
        ----------
        state : dict
            Must contain ``x``, ``y``, ``yaw`` (radians).

        Returns
        -------
        dict with keys ``vx``, ``wz``, and ``action`` (human-readable label).
        """
        self.started = True

        if self.finished:
            return {"vx": 0.0, "wz": 0.0, "action": "STOP"}

        rx, ry, ryaw = state["x"], state["y"], state["yaw"]
        tx, ty = self.waypoints[self.current_wp]

        dx = tx - rx
        dy = ty - ry
        dist = math.hypot(dx, dy)

        # Waypoint reached?
        if dist < WAYPOINT_REACH_DIST:
            self.total_waypoints_reached += 1
            self.current_wp += 1
            if self.current_wp >= len(self.waypoints) and self.loop:
                self.current_wp = 0
                self.laps += 1
            # Re-check for finished (non-loop).
            if self.finished:
                return {"vx": 0.0, "wz": 0.0, "action": "STOP"}
            # Recurse once with the new target.
            return self.decide_action(state)

        # Bearing to waypoint.
        bearing = math.atan2(dy, dx)
        heading_error = _normalise_angle(bearing - ryaw)

        # Angular velocity — proportional control.
        wz = KP_ANGULAR * heading_error
        wz = max(-MAX_WZ, min(MAX_WZ, wz))

        # Linear velocity — reduce when heading error is large.
        if abs(heading_error) > HEADING_SLOW_THRESH:
            vx = MIN_VX
        else:
            vx = MAX_VX * (1.0 - abs(heading_error) / math.pi)
            vx = max(MIN_VX, min(MAX_VX, vx))

        # Human-readable action label.
        if abs(heading_error) > 0.3:
            action = "LEFT" if heading_error > 0 else "RIGHT"
        else:
            action = "FORWARD"

        return {"vx": vx, "wz": wz, "action": action}


def state_summary(state: dict[str, Any], navigator: HuskyNavigator) -> str:
    """Build a concise text summary of the current robot state."""
    x = state.get("x", 0.0)
    y = state.get("y", 0.0)
    yaw = state.get("yaw", 0.0)

    target = navigator.target
    target_str = f"({target[0]:.1f}, {target[1]:.1f})" if target else "None (finished)"

    if target:
        dist = math.hypot(target[0] - x, target[1] - y)
        dist_str = f"{dist:.2f}m"
    else:
        dist_str = "N/A"

    return (
        f"Robot pose: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f} rad\n"
        f"Current waypoint: {navigator.current_wp + 1}/{len(navigator.waypoints)} -> {target_str}\n"
        f"Distance to waypoint: {dist_str}\n"
        f"Waypoints reached: {navigator.total_waypoints_reached}\n"
        f"Laps completed: {navigator.laps}\n"
        f"Status: {'Navigating' if not navigator.finished else 'Mission complete'}"
    )
