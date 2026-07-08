from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from dimgaai_cli.paths import ENV_FILE, FRONTEND, FRONTEND_DIST, ROOT, TOOLS_DIR

NODE_CANDIDATES = [
    # Prefer project-local portable Node (no admin) over broken system npm stubs
    lambda: _exists_cmd(str(TOOLS_DIR / "node-v22.16.0-win-x64" / "npm.cmd")),
    lambda: shutil.which("npm"),
    lambda: _exists_cmd(r"C:\Program Files\nodejs\npm.cmd"),
    lambda: _exists_cmd(os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs\npm.cmd")),
]

FFMPEG_CANDIDATES = [
    lambda: shutil.which("ffmpeg"),
    lambda: _exists_cmd(str(TOOLS_DIR / "ffmpeg" / "bin" / "ffmpeg.exe")),
    lambda: _exists_cmd(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
    lambda: _exists_cmd(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe")),
]


def _exists_cmd(path: str | None) -> str | None:
    if path and Path(path).exists():
        return path
    return None


def find_npm() -> str | None:
    for fn in NODE_CANDIDATES:
        found = fn()
        if found:
            return found
    return None


def find_ffmpeg() -> str | None:
    for fn in FFMPEG_CANDIDATES:
        found = fn()
        if found:
            return found
    return None


def _port_in_use(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def _pids_on_port_windows(port: int) -> list[int]:
    try:
        out = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    pids: set[int] = set()
    pattern = re.compile(rf":{port}\s")
    for line in out.stdout.splitlines():
        if "LISTENING" not in line and "ESTABLISHED" not in line:
            continue
        if not pattern.search(line):
            continue
        parts = line.split()
        if parts:
            try:
                pids.add(int(parts[-1]))
            except ValueError:
                continue
    return [p for p in pids if p > 0]


def _kill_pid(pid: int) -> bool:
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
            )
        else:
            import signal

            os.kill(pid, signal.SIGTERM)
        return True
    except (ProcessLookupError, OSError, subprocess.SubprocessError):
        return False


def free_port(port: int) -> bool:
    """Return True when port is free after cleanup attempts."""
    if not _port_in_use(port):
        return True
    if sys.platform == "win32":
        for pid in _pids_on_port_windows(port):
            _kill_pid(pid)
        time.sleep(0.5)
    return not _port_in_use(port)


def try_install_windows_deps(install_node: bool, install_ffmpeg: bool) -> list[str]:
    """Attempt winget installs; return list of installed package labels."""
    if platform.system() != "Windows" or not shutil.which("winget"):
        return []
    installed: list[str] = []
    specs = []
    if install_node and not find_npm():
        specs.append(("OpenJS.NodeJS.LTS", "Node.js"))
    if install_ffmpeg and not find_ffmpeg():
        specs.append(("Gyan.FFmpeg", "ffmpeg"))
    for package_id, label in specs:
        result = subprocess.run(
            [
                "winget",
                "install",
                package_id,
                "-e",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            check=False,
        )
        if result.returncode == 0:
            installed.append(label)
    return installed


def append_to_path(*dirs: str) -> None:
    current = os.environ.get("PATH", "")
    for d in dirs:
        if d and Path(d).exists() and d not in current:
            current = f"{d}{os.pathsep}{current}"
    os.environ["PATH"] = current


def refresh_tool_paths() -> None:
    from dimgaai_cli.portable_tools import refresh_portable_paths

    refresh_portable_paths()
    append_to_path(
        str(TOOLS_DIR / "node-v22.16.0-win-x64"),
        str(TOOLS_DIR / "ffmpeg" / "bin"),
        r"C:\Program Files\nodejs",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs"),
        r"C:\Program Files\ffmpeg\bin",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links"),
    )
