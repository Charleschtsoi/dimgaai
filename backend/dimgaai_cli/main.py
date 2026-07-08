from __future__ import annotations

import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dimgaai_cli.doctor import run_checks
from dimgaai_cli.paths import (
    BACKEND,
    ENV_EXAMPLE,
    ENV_FILE,
    FRONTEND,
    FRONTEND_DIST,
    ROOT,
    backend_env,
)
from dimgaai_cli.portable_tools import (
    ensure_frontend_built,
    ensure_portable_ffmpeg,
    ensure_portable_node,
    frontend_ready,
)
from dimgaai_cli.prereqs import find_ffmpeg, find_npm, refresh_tool_paths, try_install_windows_deps
from dimgaai_cli.processes import (
    prepare_ports,
    start_dev,
    start_prod,
    stop_all,
    wait_for_health,
)
from dimgaai_cli.setup_wizard import run_setup_wizard

app = typer.Typer(
    name="dimgaai",
    help="dimgaai 點解 — local CLI for Cantonese meeting support (phase 1).",
    add_completion=False,
)
console = Console()


def _ensure_backend_deps() -> None:
    try:
        import uvicorn  # noqa: F401
    except ImportError:
        console.print("[yellow]Installing backend dependencies…[/yellow]")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=str(BACKEND),
            check=True,
        )


def _print_check_table(ok: list[str], blockers: list[str], hints: list[str]) -> None:
    table = Table(title="dimgaai status", show_header=True, header_style="bold")
    table.add_column("Status", width=8)
    table.add_column("Detail")
    for item in ok:
        table.add_row("[green]OK[/green]", item)
    for item in blockers:
        table.add_row("[red]BLOCK[/red]", item)
    for item in hints:
        table.add_row("[yellow]HINT[/yellow]", item)
    console.print(table)


def _npm_env() -> dict[str, str]:
    from dimgaai_cli.portable_tools import _tool_env

    return _tool_env()


def _npm_install() -> None:
    npm = find_npm()
    if not npm:
        raise typer.Exit(code=1)
    node_modules = FRONTEND / "node_modules"
    if not node_modules.exists():
        console.print("[yellow]Running npm install…[/yellow]")
        subprocess.run(
            [npm, "install"],
            cwd=str(FRONTEND),
            env=_npm_env(),
            check=True,
        )


def _npm_build() -> None:
    _npm_install()
    npm = find_npm()
    if not npm:
        raise typer.Exit(code=1)
    console.print("[yellow]Building frontend…[/yellow]")
    subprocess.run(
        [npm, "run", "build"],
        cwd=str(FRONTEND),
        env=_npm_env(),
        check=True,
    )


def _maybe_install_deps(install_deps: bool) -> None:
    refresh_tool_paths()
    if not install_deps:
        return

    need_node = not find_npm() and not frontend_ready()
    need_ffmpeg = not find_ffmpeg()

    if sys.platform == "win32" and shutil.which("winget") and (need_node or need_ffmpeg):
        console.print("[dim]Trying winget (needs admin on some PCs)…[/dim]")
        installed = try_install_windows_deps(need_node, need_ffmpeg)
        refresh_tool_paths()
        if installed:
            console.print(f"[green]Installed via winget:[/green] {', '.join(installed)}")

    if not find_npm() and not frontend_ready():
        console.print(
            "[yellow]Downloading portable Node.js to .tools/ (no admin required)…[/yellow]"
        )
        ensure_portable_node(allow_download=True)

    if not find_ffmpeg():
        console.print(
            "[dim]Downloading portable ffmpeg to .tools/ (no admin)…[/dim]"
        )
        ensure_portable_ffmpeg(allow_download=True)

    refresh_tool_paths()


def _start_app(open_browser: bool) -> None:
    """Start dev or production server depending on what is available."""
    prepare_ports()

    if not frontend_ready():
        console.print("[yellow]Building frontend (first run only)…[/yellow]")
        if not ensure_frontend_built(allow_download=True):
            console.print(
                "[red]Could not build frontend.[/red] Check internet connection "
                "or run: [cyan]dimgaai setup[/cyan] then retry."
            )
            raise typer.Exit(code=1)

    if frontend_ready():
        env = backend_env(
            {
                "STATIC_DIR": str(FRONTEND_DIST.resolve()),
                "CORS_ORIGINS": "http://localhost:8000,http://127.0.0.1:8000",
            }
        )
        start_prod(env)
        if not wait_for_health():
            console.print("[red]Backend did not become healthy in time.[/red]")
            raise typer.Exit(code=1)
        url = "http://localhost:8000"
        mode = "Python-only (port 8000) — no system Node install needed"
    elif find_npm():
        _npm_install()
        env = backend_env()
        start_dev(env)
        url = "http://localhost:5173"
        mode = "Dev mode (port 5173)"
    else:
        console.print("[red]Cannot start UI.[/red]")
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"[bold green]dimgaai is running[/bold green]\n\n"
            f"{url}\n"
            f"[dim]{mode}[/dim]\n\n"
            "1. Open the link\n"
            "2. Open Settings (API) to enter Deepgram + Gemini keys\n"
            "3. Tap Start recording",
            title="Ready",
        )
    )
    console.print("Stop with: [cyan]dimgaai stop[/cyan]")
    if open_browser:
        webbrowser.open(url)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing .env"),
):
    """Create .env from template and install Python dependencies."""
    if ENV_FILE.exists() and not force:
        console.print(f"[green].env already exists[/green] ({ENV_FILE})")
    else:
        if not ENV_EXAMPLE.exists():
            raise typer.Exit(code=1)
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        console.print(f"[green]Created[/green] {ENV_FILE}")

    _ensure_backend_deps()
    console.print("\n[bold]Quick start:[/bold] run [cyan]dimgaai go[/cyan]")


@app.command()
def setup():
    """Interactive API key setup in the terminal (optional — browser BYOK is default)."""
    _ensure_backend_deps()
    run_setup_wizard(skip_if_configured=False)
    console.print("\n[bold]Next:[/bold] [cyan]dimgaai go[/cyan]")


@app.command()
def doctor(
    strict: bool = typer.Option(False, "--strict", help="Treat hints as failures"),
):
    """Check local prerequisites."""
    ok, blockers, hints = run_checks(strict=strict)
    _print_check_table(ok, blockers, hints)
    if blockers:
        raise typer.Exit(code=1)
    if hints and strict:
        raise typer.Exit(code=1)
    if hints:
        console.print("[yellow]Hints only — you can still run [cyan]dimgaai go[/cyan][/yellow]")
    else:
        console.print("[green]All checks passed.[/green]")


@app.command()
def go(
    install_deps: bool = typer.Option(
        True,
        "--install-deps/--no-install-deps",
        help="Try winget install for Node.js + ffmpeg on Windows",
    ),
    open_browser: bool = typer.Option(True, "--open/--no-open"),
):
    """One-command start: free ports, install deps, launch app (API keys in browser)."""
    console.print(Panel("[bold]dimgaai go[/bold] — starting in one flow…", title="dimgaai"))

    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            console.print(f"[green]Created[/green] {ENV_FILE}")

    _ensure_backend_deps()

    _maybe_install_deps(install_deps)
    refresh_tool_paths()

    ok, blockers, hints = run_checks()
    # Allow go to proceed if only blocker is "frontend not built" — we build next
    blockers = [b for b in blockers if "Frontend not built" not in b]
    if blockers:
        _print_check_table(ok, blockers, hints)
        console.print("[red]Cannot start — fix BLOCK items above.[/red]")
        raise typer.Exit(code=1)

    if hints:
        _print_check_table(ok, [], hints)

    _start_app(open_browser)


@app.command()
def dev(
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser"),
):
    """Start backend + Vite dev server (recommended for local use)."""
    _ensure_backend_deps()
    refresh_tool_paths()
    ok, blockers, hints = run_checks()
    if blockers:
        _print_check_table(ok, blockers, hints)
        console.print("[red]Fix BLOCK items or run: [cyan]dimgaai go[/cyan][/red]")
        raise typer.Exit(code=1)

    prepare_ports()
    _npm_install()
    env = backend_env()
    start_dev(env)
    url = "http://localhost:5173"
    console.print(Panel(f"[bold green]dimgaai dev running[/bold green]\n\n{url}", title="dimgaai"))
    console.print("Stop with: [cyan]dimgaai stop[/cyan]")
    if open_browser:
        webbrowser.open(url)


@app.command("start")
def start_cmd(
    rebuild: bool = typer.Option(False, "--rebuild", help="Rebuild frontend"),
    open_browser: bool = typer.Option(True, "--open/--no-open"),
):
    """Build frontend and serve everything on http://localhost:8000."""
    _ensure_backend_deps()
    refresh_tool_paths()
    if rebuild or not FRONTEND_DIST.exists():
        _npm_build()

    prepare_ports()
    env = backend_env(
        {
            "STATIC_DIR": str(FRONTEND_DIST.resolve()),
            "CORS_ORIGINS": "http://localhost:8000,http://127.0.0.1:8000",
        }
    )
    start_prod(env)
    if not wait_for_health():
        console.print("[red]Backend did not become healthy in time.[/red]")
        raise typer.Exit(code=1)
    url = "http://localhost:8000"
    console.print(Panel(f"[bold green]dimgaai running[/bold green]\n\n{url}", title="dimgaai"))
    console.print("Stop with: [cyan]dimgaai stop[/cyan]")
    if open_browser:
        webbrowser.open(url)


@app.command()
def stop():
    """Stop processes started by dimgaai dev or start."""
    stopped = stop_all()
    prepare_ports()
    if stopped:
        console.print(f"[green]Stopped {len(stopped)} process(es).[/green]")
    else:
        console.print("[yellow]No dimgaai processes recorded (ports cleared if possible).[/yellow]")


@app.command()
def test():
    """Run automated demo checklist."""
    script = BACKEND / "scripts" / "demo_checklist.py"
    subprocess.run([sys.executable, str(script), "--dry-run"], cwd=str(ROOT), check=False)


@app.command()
def share(
    mode: str = typer.Option("dev", "--mode", "-m", help="dev (port 5173) or start (port 8000)"),
):
    """Start app and print a public HTTPS URL via Cloudflare Tunnel (if installed)."""
    cloudflared = shutil.which("cloudflared")
    if not cloudflared:
        console.print("[red]cloudflared not found.[/red]")
        console.print("Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        console.print("\nOr use local only: [cyan]dimgaai go[/cyan] → http://localhost:5173")
        raise typer.Exit(code=1)

    if mode == "dev":
        dev(open_browser=False)
        tunnel_url = "http://localhost:5173"
    else:
        start_cmd(rebuild=False, open_browser=False)
        tunnel_url = "http://localhost:8000"

    console.print(f"[yellow]Starting tunnel to {tunnel_url}…[/yellow]")
    console.print("[dim]Press Ctrl+C to stop the tunnel. Run 'dimgaai stop' to stop the app.[/dim]\n")
    try:
        subprocess.run([cloudflared, "tunnel", "--url", tunnel_url], check=False)
    except KeyboardInterrupt:
        console.print("\n[yellow]Tunnel stopped.[/yellow]")


@app.command()
def version():
    """Show version."""
    console.print("dimgaai CLI 0.4.0 (local phase 1)")


def run() -> None:
    app()


if __name__ == "__main__":
    run()
