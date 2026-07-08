from __future__ import annotations

import platform
import shutil
import socket
import sys
from pathlib import Path

from dimgaai_cli.paths import ENV_FILE, FRONTEND, ROOT

REQUIRED_ENV_KEYS = ("DEEPGRAM_API_KEY", "OPENAI_API_KEY")
OPTIONAL_ENV_KEYS = ("ANTHROPIC_API_KEY", "TAVILY_API_KEY")


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _read_env_keys() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    values: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        values[key.strip()] = val.strip()
    return values


def run_checks() -> tuple[list[str], list[str]]:
    ok: list[str] = []
    warn: list[str] = []

    py = sys.version_info
    if py >= (3, 11):
        ok.append(f"Python {py.major}.{py.minor}.{py.micro}")
    else:
        warn.append(f"Python 3.11+ recommended (found {py.major}.{py.minor})")

    if shutil.which("ffmpeg"):
        ok.append("ffmpeg found (webm decode)")
    else:
        warn.append("ffmpeg not found - install for mic transcription (choco install ffmpeg)")

    if shutil.which("node"):
        ok.append(f"Node.js ({shutil.which('node')})")
    else:
        warn.append("Node.js not found - required for frontend")

    if shutil.which("npm"):
        ok.append("npm found")
    elif FRONTEND.exists():
        warn.append("npm not found - required for frontend")

    if ENV_FILE.exists():
        ok.append(f".env present ({ENV_FILE})")
        env = _read_env_keys()
        missing = [k for k in REQUIRED_ENV_KEYS if not env.get(k)]
        if missing:
            warn.append(
                f"Missing keys in .env: {', '.join(missing)} "
                "(or use BYOK in the browser UI)"
            )
        else:
            ok.append("Required API keys set in .env")
    else:
        warn.append(f"No .env - run: dimgaai init")

    for port, label in ((8000, "backend"), (5173, "frontend dev")):
        if _port_free(port):
            ok.append(f"Port {port} free ({label})")
        else:
            warn.append(f"Port {port} in use ({label}) - run: dimgaai stop")

    if not (ROOT / "backend" / "app" / "main.py").exists():
        warn.append(f"Repo root looks wrong: {ROOT}")
    else:
        ok.append(f"Project root: {ROOT}")

    if platform.system() == "Windows":
        ok.append("OS: Windows (use scripts\\dimgaai.ps1 or python -m dimgaai_cli)")

    return ok, warn
