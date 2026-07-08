from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from dimgaai_cli.paths import BACKEND, FRONTEND, clear_state, load_state, save_state


def _popen(cmd: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen:
    kwargs: dict = {
        "cwd": str(cwd),
        "env": env,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, **kwargs)


def start_dev(env: dict[str, str]) -> None:
    python = sys.executable
    backend = _popen(
        [python, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        BACKEND,
        env,
    )
    npm = shutil_which("npm")
    if not npm:
        raise RuntimeError("npm not found")
    frontend = _popen([npm, "run", "dev"], FRONTEND, os.environ.copy())
    save_state(
        {
            "mode": "dev",
            "pids": [backend.pid, frontend.pid],
            "url": "http://localhost:5173",
        }
    )


def start_prod(env: dict[str, str]) -> None:
    python = sys.executable
    backend = _popen(
        [python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        BACKEND,
        env,
    )
    save_state(
        {
            "mode": "start",
            "pids": [backend.pid],
            "url": "http://localhost:8000",
        }
    )


def stop_all() -> list[int]:
    state = load_state()
    stopped: list[int] = []
    for pid in state.get("pids", []):
        if _kill_pid(pid):
            stopped.append(pid)
    clear_state()
    return stopped


def _kill_pid(pid: int) -> bool:
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
            )
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        return True
    except (ProcessLookupError, OSError, subprocess.SubprocessError):
        return False


def wait_for_health(url: str = "http://127.0.0.1:8000/health", timeout: float = 60) -> bool:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)
    return False


def shutil_which(cmd: str) -> str | None:
    import shutil

    return shutil.which(cmd)
