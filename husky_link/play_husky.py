"""Play Husky navigation using OmniLink tool calling.

The AI agent calls the ``make_move`` tool, which acts as a local
Husky navigation controller.  The model never sees the robot — it simply
triggers the tool.  The tool reads the robot pose, computes steering
toward the next waypoint, and drives the robot accordingly.

This keeps API credit usage to a minimum (one call to kick off).

Usage
-----
    python -u play_husky.py
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any

# ── Path setup ─────────────────────────────────────────────────────────
_HERE = str(pathlib.Path(__file__).resolve().parent)
LIB_PATH = str(pathlib.Path(__file__).resolve().parents[3] / "omnilink-lib" / "src")
if _HERE in sys.path:
    sys.path.remove(_HERE)
if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)

from omnilink.tool_runner import ToolRunner

if _HERE not in sys.path:
    sys.path.append(_HERE)

from husky_api import get_state, send_action, drive
from husky_engine import HuskyNavigator, state_summary


class HuskyRunner(ToolRunner):
    agent_name = "husky-agent"
    display_name = "Husky"
    tool_description = "Steer toward the next waypoint."
    poll_interval = 0.05
    memory_every = 10
    ask_every = 30
    commands = "stop_game, pause_game, resume_game"

    def __init__(self) -> None:
        self._navigator = HuskyNavigator(loop=True)
        self._last_wp = -1
        self._last_laps = 0

    def get_state(self) -> dict[str, Any]:
        return get_state()

    def execute_action(self, state: dict[str, Any]) -> None:
        cmd = self._navigator.decide_action(state)
        try:
            drive(cmd["vx"], cmd["wz"])
        except Exception:
            pass

    def state_summary(self, state: dict[str, Any]) -> str:
        return state_summary(state, self._navigator)

    def is_game_over(self, state: dict[str, Any]) -> bool:
        return self._navigator.finished

    def game_over_message(self, state: dict[str, Any]) -> str:
        return f"MISSION COMPLETE — Waypoints reached: {self._navigator.total_waypoints_reached}"

    def log_events(self, state: dict[str, Any]) -> None:
        nav = self._navigator
        if nav.current_wp != self._last_wp:
            target = nav.target
            target_str = f"({target[0]:.1f}, {target[1]:.1f})" if target else "done"
            print(f"  Waypoint {nav.current_wp + 1}/{len(nav.waypoints)} -> {target_str}  [reached: {nav.total_waypoints_reached}]")
            self._last_wp = nav.current_wp
        if nav.laps != self._last_laps:
            print(f"  ** Lap {nav.laps} completed!")
            self._last_laps = nav.laps


if __name__ == "__main__":
    HuskyRunner().run()
