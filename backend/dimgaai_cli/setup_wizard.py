from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console

from dimgaai_cli.doctor import _read_env_keys
from dimgaai_cli.paths import ENV_EXAMPLE, ENV_FILE

console = Console()

SIGNUP_LINKS = {
    "deepgram": "https://console.deepgram.com/",
    "openai": "https://platform.openai.com/api-keys",
    "anthropic": "https://console.anthropic.com/",
    "gemini": "https://aistudio.google.com/apikey",
}

PROVIDERS = {
    "1": ("openai", "OpenAI", "OPENAI_API_KEY", 2),
    "2": ("anthropic", "Anthropic", "ANTHROPIC_API_KEY", 3),
    "3": ("gemini", "Google Gemini", "GOOGLE_API_KEY", 2),
}


def _ensure_env_file() -> None:
    if not ENV_FILE.exists():
        if not ENV_EXAMPLE.exists():
            raise typer.Exit(code=1)
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        console.print(f"[green]Created[/green] {ENV_FILE}")


def _update_env(updates: dict[str, str]) -> None:
    lines: list[str] = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    existing = {
        k: i
        for i, line in enumerate(lines)
        if "=" in line
        for k in [line.split("=", 1)[0].strip()]
    }
    for key, value in updates.items():
        entry = f"{key}={value}"
        if key in existing:
            lines[existing[key]] = entry
        else:
            lines.append(entry)
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def keys_configured() -> bool:
    if not ENV_FILE.exists():
        return False
    env = _read_env_keys()
    if not env.get("DEEPGRAM_API_KEY"):
        return False
    provider = env.get("LLM_PROVIDER", "gemini").lower()
    llm_key = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }.get(provider, "GOOGLE_API_KEY")
    if not env.get(llm_key):
        return False
    if provider == "anthropic":
        embed = env.get("EMBEDDING_PROVIDER", "google").lower()
        if embed == "google":
            return bool(env.get("GOOGLE_API_KEY"))
        return bool(env.get("OPENAI_API_KEY"))
    return True


def _count_keys(env: dict[str, str], provider: str, key_count: int) -> int:
    done = 0
    if env.get("DEEPGRAM_API_KEY"):
        done += 1
    llm_key_name = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }.get(provider, "GOOGLE_API_KEY")
    if env.get(llm_key_name):
        done += 1
    if key_count >= 3 and provider == "anthropic":
        embed = env.get("EMBEDDING_PROVIDER", "google").lower()
        if embed == "google" and env.get("GOOGLE_API_KEY"):
            done += 1
        elif embed == "openai" and env.get("OPENAI_API_KEY"):
            done += 1
    return done


def run_setup_wizard(*, skip_if_configured: bool = True) -> bool:
    """Interactive API key setup. Returns True if keys are ready (or user chose BYOK)."""
    _ensure_env_file()
    if skip_if_configured and keys_configured():
        console.print("[green]API keys already in .env (2/2 or 3/3)[/green]")
        return True

    console.print(
        "\n[bold]Live meetings need 2 APIs[/bold]\n"
        "  1. [cyan]Deepgram[/cyan] - microphone transcription (Cantonese)\n"
        "  2. [cyan]One LLM[/cyan] - analysis, fact-check, questions\n"
        "(Press Enter to skip any field - use browser BYOK later)\n"
    )
    console.print(f"Deepgram signup: {SIGNUP_LINKS['deepgram']}\n")

    deepgram = typer.prompt("Deepgram API key (1/2)", default="", show_default=False)
    console.print(
        "LLM provider: [cyan]3[/cyan]=Gemini (recommended, 2 keys)  "
        "[cyan]1[/cyan]=OpenAI  [cyan]2[/cyan]=Anthropic (3 keys)"
    )
    choice = typer.prompt("Choose LLM provider", default="3")
    provider, label, llm_env_key, key_count = PROVIDERS.get(choice, PROVIDERS["3"])
    console.print(f"{label} signup: {SIGNUP_LINKS.get(provider, '')}")
    llm_key = typer.prompt(f"{label} API key (2/{key_count})", default="", show_default=False)

    updates: dict[str, str] = {"LLM_PROVIDER": provider}
    if deepgram.strip():
        updates["DEEPGRAM_API_KEY"] = deepgram.strip()
    if llm_key.strip():
        updates[llm_env_key] = llm_key.strip()

    if provider == "anthropic":
        updates["EMBEDDING_PROVIDER"] = "google"
        console.print(f"Google signup (embeddings): {SIGNUP_LINKS['gemini']}")
        embed_key = typer.prompt(
            "Google API key for RAG embeddings (3/3)", default="", show_default=False
        )
        if embed_key.strip():
            updates["GOOGLE_API_KEY"] = embed_key.strip()

    if updates:
        _update_env(updates)
        console.print(f"[green]Saved[/green] {ENV_FILE}")

    env = _read_env_keys()
    done = _count_keys(env, provider, key_count)
    console.print(f"\n[bold]Keys configured: {done}/{key_count}[/bold]")

    if done < key_count:
        console.print(
            "[yellow]Some keys skipped - open the app and use API settings (BYOK) before recording.[/yellow]"
        )
    return True
