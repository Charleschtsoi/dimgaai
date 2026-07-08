from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

GITHUB_REPO = os.environ.get("DIMGAAI_REPO", "Charleschtsoi/dimgaai")
GITHUB_BRANCH = os.environ.get("DIMGAAI_BRANCH", "main")
ZIP_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"


def default_home() -> Path:
    override = os.environ.get("DIMGAAI_HOME")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home())
        return Path(base) / "dimgaai"
    return Path.home() / ".local" / "share" / "dimgaai"


def install_app_dir() -> Path:
    return default_home() / "app"


def _dev_repo_root() -> Path | None:
    """Return repo root when running from a git checkout."""
    here = Path(__file__).resolve()
    candidate = here.parents[2]
    if (candidate / "backend" / "app" / "main.py").exists():
        return candidate
    return None


def resolve_root() -> Path:
    env_root = os.environ.get("DIMGAAI_ROOT")
    if env_root:
        return Path(env_root)
    dev = _dev_repo_root()
    if dev:
        return dev
    return install_app_dir()


def app_installed(root: Path | None = None) -> bool:
    root = root or resolve_root()
    return (root / "backend" / "app" / "main.py").exists()


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    urlretrieve(url, tmp)  # noqa: S310
    tmp.replace(dest)


def download_app(*, force: bool = False) -> Path:
    """Download the full app from GitHub into the local install directory."""
    target = install_app_dir()
    if app_installed(target) and not force:
        return target

    console.print(
        f"[yellow]Downloading dimgaai from GitHub[/yellow] ({GITHUB_REPO}) …"
    )
    console.print(f"[dim]Install location: {target}[/dim]")

    home = default_home()
    home.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=str(home)) as tmpdir:
        zip_path = Path(tmpdir) / "repo.zip"
        extract_dir = Path(tmpdir) / "extract"
        extract_dir.mkdir()

        try:
            _download(ZIP_URL, zip_path)
        except Exception as exc:
            console.print(f"[red]Download failed:[/red] {exc}")
            console.print(
                "[dim]Check internet connection, or clone the repo manually.[/dim]"
            )
            raise SystemExit(1) from exc

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # GitHub zip extracts to dimgaai-main/ or repo-branch/
        extracted_roots = [p for p in extract_dir.iterdir() if p.is_dir()]
        if not extracted_roots:
            console.print("[red]Downloaded archive was empty.[/red]")
            raise SystemExit(1)
        source = extracted_roots[0]
        if not (source / "backend" / "app" / "main.py").exists():
            console.print("[red]Downloaded archive does not look like dimgaai.[/red]")
            raise SystemExit(1)

        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        shutil.move(str(source), str(target))

    version_file = home / "version.txt"
    version_file.write_text(f"{GITHUB_REPO}@{GITHUB_BRANCH}\n", encoding="utf-8")
    console.print(f"[green]dimgaai installed to[/green] {target}")
    return target


def ensure_app(*, force: bool = False) -> Path:
    """Ensure app files exist; download if running from pip-installed CLI only."""
    from dimgaai_cli.paths import reconfigure_paths

    dev = _dev_repo_root()
    if dev and not force:
        reconfigure_paths(dev)
        return dev

    target = install_app_dir()
    if not app_installed(target) or force:
        target = download_app(force=force)
    reconfigure_paths(target)
    return target
