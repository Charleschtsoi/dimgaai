from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
STATE_DIR = ROOT / ".dimgaai"
STATE_FILE = STATE_DIR / "state.json"
TOOLS_DIR = ROOT / ".tools"
FRONTEND_DIST = FRONTEND / "dist"


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def clear_state() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def backend_env(extra: dict | None = None) -> dict[str, str]:
    env = os.environ.copy()
    path = env.get("PATH", "")
    for tool_dir in (
        TOOLS_DIR / "node-v22.16.0-win-x64",
        TOOLS_DIR / "ffmpeg" / "bin",
    ):
        tool_path = str(tool_dir)
        if tool_dir.exists() and tool_path not in path:
            path = f"{tool_path}{os.pathsep}{path}"
    env["PATH"] = path
    env["PYTHONPATH"] = str(BACKEND)
    if extra:
        env.update(extra)
    return env
