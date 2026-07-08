from __future__ import annotations

import platform
import shutil
import socket
import sys
from pathlib import Path

from dimgaai_cli.paths import ENV_FILE, FRONTEND, FRONTEND_DIST, ROOT


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


def run_checks(*, strict: bool = False) -> tuple[list[str], list[str], list[str]]:
    """
    Returns (ok, blockers, hints).
    blockers prevent dev/start; hints are optional (BYOK, ffmpeg, etc.).
    """
    ok: list[str] = []
    blockers: list[str] = []
    hints: list[str] = []
    recording_hints: list[str] = []
    optional_hints: list[str] = []

    py = sys.version_info
    if py >= (3, 11):
        ok.append(f"Python {py.major}.{py.minor}.{py.micro}")
    else:
        blockers.append(f"Python 3.11+ required (found {py.major}.{py.minor})")

    from dimgaai_cli.portable_tools import frontend_ready
    from dimgaai_cli.prereqs import find_ffmpeg, find_npm

    npm = find_npm()
    if npm:
        ok.append(f"npm found ({npm})")
    elif frontend_ready():
        ok.append("Frontend pre-built — Node.js not required to start")
    elif FRONTEND.exists():
        blockers.append(
            "Frontend not built yet — dimgaai go will download portable Node "
            "to .tools/ (no admin) and build automatically"
        )

    if find_ffmpeg():
        ok.append("ffmpeg found (mic transcription)")
    else:
        optional_hints.append(
            "ffmpeg not found - mic needs it (winget install Gyan.FFmpeg)"
        )

    if ENV_FILE.exists():
        ok.append(".env present")
        env = _read_env_keys()
        provider = env.get("LLM_PROVIDER", "gemini").lower()
        key_total = 3 if provider == "anthropic" else 2
        key_done = 0
        if env.get("DEEPGRAM_API_KEY"):
            key_done += 1
        else:
            recording_hints.append(
                "DEEPGRAM_API_KEY missing - Deepgram for mic (setup or BYOK)"
            )
        llm_key_name = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }.get(provider, "GOOGLE_API_KEY")
        if env.get(llm_key_name):
            key_done += 1
        else:
            recording_hints.append(
                f"{llm_key_name} missing - LLM for analysis (setup or BYOK)"
            )
        if provider == "anthropic":
            embed = env.get("EMBEDDING_PROVIDER", "google").lower()
            if embed == "google" and env.get("GOOGLE_API_KEY"):
                key_done += 1
            elif embed == "openai" and env.get("OPENAI_API_KEY"):
                key_done += 1
            else:
                recording_hints.append(
                    "Embedding key missing - Google or OpenAI for PDF fact-check"
                )
        if key_done >= key_total:
            ok.append(f"Recording keys: {key_done}/{key_total} ({provider})")
        elif key_done > 0:
            recording_hints.append(f"Recording keys: {key_done}/{key_total} configured")
    else:
        recording_hints.append("No .env yet - dimgaai go will create one")

    for port, label in ((8000, "backend"), (5173, "frontend")):
        if _port_free(port):
            ok.append(f"Port {port} free ({label})")
        else:
            optional_hints.append(f"Port {port} in use ({label}) - dimgaai go will free it")

    if not (ROOT / "backend" / "app" / "main.py").exists():
        blockers.append(f"Project root looks wrong: {ROOT}")
    else:
        ok.append(f"Project root: {ROOT}")

    if platform.system() == "Windows":
        ok.append("OS: Windows")

    hints.extend(recording_hints)
    hints.extend(optional_hints)

    if strict and hints:
        blockers.extend(hints)
        hints = []

    return ok, blockers, hints
