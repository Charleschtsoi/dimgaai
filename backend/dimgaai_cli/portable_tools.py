from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from dimgaai_cli.paths import FRONTEND, FRONTEND_DIST, ROOT, TOOLS_DIR

# Windows x64 Node LTS — extracted under .tools/ (no admin required)
NODE_VERSION = "22.16.0"
NODE_FOLDER = f"node-v{NODE_VERSION}-win-x64"
NODE_ZIP_URL = f"https://nodejs.org/dist/v{NODE_VERSION}/{NODE_FOLDER}.zip"
PORTABLE_NODE_ROOT = TOOLS_DIR / NODE_FOLDER
PORTABLE_NPM = PORTABLE_NODE_ROOT / "npm.cmd"
PORTABLE_NODE = PORTABLE_NODE_ROOT / "node.exe"

FFMPEG_ZIP_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)
PORTABLE_FFMPEG = TOOLS_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"


def portable_node_installed() -> bool:
    return PORTABLE_NPM.exists()


def portable_ffmpeg_installed() -> bool:
    return PORTABLE_FFMPEG.exists()


def refresh_portable_paths() -> None:
    """Add project-local tools to PATH for this process."""
    os.environ["PATH"] = _prepend_path(os.environ.get("PATH", ""))


def _prepend_path(path: str) -> str:
    parts: list[str] = []
    if portable_node_installed():
        parts.append(str(PORTABLE_NODE_ROOT))
    if portable_ffmpeg_installed():
        parts.append(str(PORTABLE_FFMPEG.parent))
    for p in parts:
        if p not in path:
            path = f"{p}{os.pathsep}{path}"
    return path


def _tool_env() -> dict[str, str]:
    """Environment for npm/ffmpeg subprocesses — portable tools first on PATH."""
    env = os.environ.copy()
    env["PATH"] = _prepend_path(env.get("PATH", ""))
    return env


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urlretrieve(url, tmp)  # noqa: S310 — trusted vendor URLs only
    tmp.replace(dest)


def ensure_portable_node(*, allow_download: bool = True) -> bool:
    """Install Node.js into .tools/ without admin. Returns True if npm is available."""
    from dimgaai_cli.prereqs import find_npm

    refresh_portable_paths()
    if find_npm():
        return True
    if not allow_download or platform.system() != "Windows":
        return False
    if portable_node_installed():
        refresh_portable_paths()
        return find_npm() is not None

    zip_path = TOOLS_DIR / f"{NODE_FOLDER}.zip"
    try:
        print(f"Downloading portable Node.js {NODE_VERSION} to {TOOLS_DIR} …")
        _download(NODE_ZIP_URL, zip_path)
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(TOOLS_DIR)
        zip_path.unlink(missing_ok=True)
        refresh_portable_paths()
        return find_npm() is not None
    except Exception as exc:
        print(f"Portable Node download failed: {exc}")
        return False


def ensure_portable_ffmpeg(*, allow_download: bool = True) -> bool:
    from dimgaai_cli.prereqs import find_ffmpeg

    refresh_portable_paths()
    if find_ffmpeg():
        return True
    if not allow_download or platform.system() != "Windows":
        return False
    if portable_ffmpeg_installed():
        refresh_portable_paths()
        return True

    zip_path = TOOLS_DIR / "ffmpeg-portable.zip"
    try:
        print(f"Downloading portable ffmpeg to {TOOLS_DIR} …")
        _download(FFMPEG_ZIP_URL, zip_path)
        extract_tmp = TOOLS_DIR / "ffmpeg_extract"
        if extract_tmp.exists():
            shutil.rmtree(extract_tmp, ignore_errors=True)
        extract_tmp.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_tmp)
        zip_path.unlink(missing_ok=True)
        # Zip contains ffmpeg-*-win64-gpl/bin/ffmpeg.exe
        bin_dir = None
        for path in extract_tmp.rglob("ffmpeg.exe"):
            bin_dir = path.parent
            break
        if not bin_dir:
            return False
        target_bin = TOOLS_DIR / "ffmpeg" / "bin"
        if target_bin.exists():
            shutil.rmtree(target_bin.parent, ignore_errors=True)
        target_bin.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(bin_dir), str(target_bin))
        shutil.rmtree(extract_tmp, ignore_errors=True)
        refresh_portable_paths()
        return find_ffmpeg() is not None
    except Exception as exc:
        print(f"Portable ffmpeg download failed: {exc}")
        return False


def frontend_ready() -> bool:
    return (FRONTEND_DIST / "index.html").exists()


def _clean_partial_node_modules() -> None:
    node_modules = FRONTEND / "node_modules"
    if node_modules.exists():
        shutil.rmtree(node_modules, ignore_errors=True)


def build_frontend() -> bool:
    from dimgaai_cli.prereqs import find_npm

    refresh_portable_paths()
    npm = find_npm()
    if not npm:
        return False
    if not (FRONTEND / "package.json").exists():
        return False
    env = _tool_env()
    node_modules = FRONTEND / "node_modules"
    if not node_modules.exists():
        print("Running npm install (first time, may take a few minutes)…")
        result = subprocess.run(
            [npm, "install"],
            cwd=str(FRONTEND),
            env=env,
            check=False,
        )
        if result.returncode != 0:
            print("npm install failed — cleaning partial node_modules for retry…")
            _clean_partial_node_modules()
            return False
    print("Building frontend…")
    result = subprocess.run(
        [npm, "run", "build"],
        cwd=str(FRONTEND),
        env=env,
        check=False,
    )
    return result.returncode == 0 and frontend_ready()


def ensure_frontend_built(*, allow_download: bool = True) -> bool:
    if frontend_ready():
        return True
    if ensure_portable_node(allow_download=allow_download):
        return build_frontend()
    return False
