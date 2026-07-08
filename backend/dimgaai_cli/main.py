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
from dimgaai_cli.processes import (
    start_dev,
    start_prod,
    stop_all,
    wait_for_health,
)

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
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Edit .env and add DEEPGRAM_API_KEY + OPENAI_API_KEY")
    console.print("     (or skip and use BYOK in the browser UI)")
    console.print("  2. Run: [cyan]dimgaai doctor[/cyan]")
    console.print("  3. Run: [cyan]dimgaai dev[/cyan]")


@app.command()
def doctor():
    """Check local prerequisites (Python, ffmpeg, Node, .env, ports)."""
    ok, warn = run_checks()
    table = Table(title="dimgaai doctor", show_header=True, header_style="bold")
    table.add_column("Status", width=8)
    table.add_column("Detail")
    for item in ok:
        table.add_row("[green]OK[/green]", item)
    for item in warn:
        table.add_row("[yellow]WARN[/yellow]", item)
    console.print(table)
    if warn:
        raise typer.Exit(code=1)
    console.print("[green]All checks passed.[/green]")


def _npm_install() -> None:
    npm = shutil.which("npm")
    if not npm:
        raise typer.Exit(code=1)
    node_modules = FRONTEND / "node_modules"
    if not node_modules.exists():
        console.print("[yellow]Running npm install…[/yellow]")
        subprocess.run([npm, "install"], cwd=str(FRONTEND), check=True)


def _npm_build() -> None:
    _npm_install()
    npm = shutil.which("npm")
    console.print("[yellow]Building frontend…[/yellow]")
    subprocess.run([npm, "run", "build"], cwd=str(FRONTEND), check=True)


@app.command()
def dev(
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser"),
):
    """Start backend + Vite dev server (recommended for local use)."""
    _ensure_backend_deps()
    ok, warn = run_checks()
    if any("Port 8000 in use" in w or "Port 5173 in use" in w for w in warn):
        console.print("[red]Ports busy. Run: dimgaai stop[/red]")
        raise typer.Exit(code=1)

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
    if rebuild or not FRONTEND_DIST.exists():
        _npm_build()

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
    if stopped:
        console.print(f"[green]Stopped {len(stopped)} process(es).[/green]")
    else:
        console.print("[yellow]No dimgaai processes recorded.[/yellow]")


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
        console.print("\nOr use local only: [cyan]dimgaai dev[/cyan] → http://localhost:5173")
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
    console.print("dimgaai CLI 0.3.0 (local phase 1)")


def run() -> None:
    app()


if __name__ == "__main__":
    run()
