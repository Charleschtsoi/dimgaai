from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen, urlretrieve

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

GITHUB_REPO = os.environ.get("DIMGAAI_REPO", "Charleschtsoi/dimgaai")
GITHUB_BRANCH = os.environ.get("DIMGAAI_BRANCH", "main")
ZIP_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
GITHUB_COMMITS_URL = (
    f"https://api.github.com/repos/{GITHUB_REPO}/commits/{GITHUB_BRANCH}"
)
UPDATE_CHECK_TIMEOUT_S = 5.0


@dataclass
class UpdateCheck:
    update_available: bool
    local_sha: str | None = None
    remote_sha: str | None = None
    source: str = "bootstrap"
    message: str = ""


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


def version_file_path() -> Path:
    return default_home() / "version.txt"


def read_installed_sha() -> str | None:
    version_file = version_file_path()
    if not version_file.exists():
        return None
    lines = [ln.strip() for ln in version_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(lines) >= 2:
        return lines[1]
    return None


def write_version_file(commit_sha: str) -> None:
    home = default_home()
    home.mkdir(parents=True, exist_ok=True)
    version_file = version_file_path()
    version_file.write_text(
        f"{GITHUB_REPO}@{GITHUB_BRANCH}\n{commit_sha}\n",
        encoding="utf-8",
    )


def fetch_remote_commit_sha(*, timeout: float = UPDATE_CHECK_TIMEOUT_S) -> str | None:
    request = Request(
        GITHUB_COMMITS_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "dimgaai-cli",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.debug("Remote version check failed: %s", exc)
        return None
    sha = payload.get("sha")
    return str(sha) if sha else None


def uses_bootstrap_install(root: Path | None = None) -> bool:
    root = root or resolve_root()
    return root.resolve() == install_app_dir().resolve()


def check_git_updates(root: Path) -> UpdateCheck:
    if not shutil.which("git"):
        return UpdateCheck(
            update_available=False,
            source="git",
            message="git not found on PATH",
        )
    if not (root / ".git").is_dir():
        return UpdateCheck(update_available=False, source="git")

    try:
        subprocess.run(
            ["git", "fetch", "--quiet", "origin", GITHUB_BRANCH],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        remote = subprocess.run(
            ["git", "rev-parse", f"origin/{GITHUB_BRANCH}"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        return UpdateCheck(
            update_available=False,
            source="git",
            message=str(exc),
        )

    return UpdateCheck(
        update_available=local != remote,
        local_sha=local,
        remote_sha=remote,
        source="git",
    )


def check_bootstrap_updates() -> UpdateCheck:
    remote_sha = fetch_remote_commit_sha()
    if not remote_sha:
        return UpdateCheck(
            update_available=False,
            source="bootstrap",
            message="could not reach GitHub",
        )

    local_sha = read_installed_sha()
    if not local_sha:
        return UpdateCheck(
            update_available=False,
            local_sha=None,
            remote_sha=remote_sha,
            source="bootstrap",
            message="installed version unknown — run bootstrap --force once to enable update checks",
        )

    return UpdateCheck(
        update_available=local_sha != remote_sha,
        local_sha=local_sha,
        remote_sha=remote_sha,
        source="bootstrap",
    )


def check_for_updates(root: Path | None = None) -> UpdateCheck:
    root = root or resolve_root()
    dev = _dev_repo_root()
    if dev and root.resolve() == dev.resolve() and (root / ".git").is_dir():
        return check_git_updates(root)
    if uses_bootstrap_install(root):
        return check_bootstrap_updates()
    if (root / ".git").is_dir():
        return check_git_updates(root)
    return UpdateCheck(
        update_available=False,
        source="bootstrap",
        message="update checks only apply to git clones or bootstrap installs",
    )


def invalidate_frontend_build() -> None:
    from dimgaai_cli.paths import FRONTEND_DIST

    if FRONTEND_DIST.exists():
        shutil.rmtree(FRONTEND_DIST, ignore_errors=True)


def _git_pull(root: Path) -> None:
    if not shutil.which("git"):
        console.print("[red]git not found on PATH.[/red]")
        raise SystemExit(1)
    console.print(f"[yellow]Pulling latest from origin/{GITHUB_BRANCH}…[/yellow]")
    result = subprocess.run(
        ["git", "pull", "--ff-only", "origin", GITHUB_BRANCH],
        cwd=str(root),
        check=False,
    )
    if result.returncode != 0:
        console.print("[red]git pull failed.[/red] Resolve conflicts manually, then retry.")
        raise SystemExit(1)
    invalidate_frontend_build()
    console.print("[green]Repository updated.[/green]")


def apply_update(*, root: Path | None = None) -> Path:
    """Pull latest changes for git clones or re-download bootstrap installs."""
    from dimgaai_cli.paths import reconfigure_paths

    root = root or resolve_root()
    dev = _dev_repo_root()
    if dev and root.resolve() == dev.resolve() and (root / ".git").is_dir():
        _git_pull(root)
        reconfigure_paths(root)
        return root
    if (root / ".git").is_dir() and not uses_bootstrap_install(root):
        _git_pull(root)
        reconfigure_paths(root)
        return root

    target = download_app(force=True)
    reconfigure_paths(target)
    return target


def maybe_check_and_apply_updates(*, interactive: bool = True) -> bool:
    """Check GitHub for updates; optionally download/pull. Returns True if updated."""
    result = check_for_updates()
    if result.message and not result.update_available:
        if result.local_sha is None and "unknown" in result.message:
            console.print(f"[dim]{result.message}[/dim]")
        elif result.message != "update checks only apply to git clones or bootstrap installs":
            logger.debug("Update check: %s", result.message)
        return False

    if not result.update_available:
        if result.local_sha and result.remote_sha:
            console.print(
                f"[dim]dimgaai is up to date ({result.local_sha[:7]})[/dim]"
            )
        return False

    local_label = (result.local_sha or "?")[:7]
    remote_label = (result.remote_sha or "?")[:7]
    action = "git pull" if result.source == "git" else "download from GitHub"
    console.print(
        f"[yellow]Update available[/yellow] "
        f"({local_label} → {remote_label}) — {action}"
    )

    should_update = True
    if interactive and sys.stdin.isatty():
        import typer

        should_update = typer.confirm("Update now?", default=True)
    elif interactive:
        console.print(
            "[dim]Run [cyan]dimgaai bootstrap --force[/cyan] "
            "or [cyan]git pull[/cyan] to update.[/dim]"
        )
        return False

    if not should_update:
        console.print("[dim]Skipped update — continuing with current version.[/dim]")
        return False

    apply_update()
    return True


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

    env_backup: str | None = None
    tools_backup: Path | None = None
    if target.exists() and force:
        env_path = target / ".env"
        if env_path.exists():
            env_backup = env_path.read_text(encoding="utf-8")
        tools_dir = target / ".tools"
        if tools_dir.exists():
            tools_backup = Path(tempfile.mkdtemp(dir=str(home), prefix="tools-backup-"))
            shutil.copytree(tools_dir, tools_backup / ".tools", dirs_exist_ok=True)

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

    if env_backup is not None:
        (target / ".env").write_text(env_backup, encoding="utf-8")
    if tools_backup is not None:
        shutil.copytree(
            tools_backup / ".tools",
            target / ".tools",
            dirs_exist_ok=True,
        )
        shutil.rmtree(tools_backup, ignore_errors=True)

    remote_sha = fetch_remote_commit_sha()
    if remote_sha:
        write_version_file(remote_sha)
    else:
        version_file_path().write_text(
            f"{GITHUB_REPO}@{GITHUB_BRANCH}\n",
            encoding="utf-8",
        )

    invalidate_frontend_build()
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
