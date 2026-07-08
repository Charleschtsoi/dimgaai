# dimgaai 點解

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Real-time Cantonese meeting assistant: live transcription, fact-check verdicts, and follow-up questions.

Repo: https://github.com/Charleschtsoi/dimgaai

---

## Quick start (recommended)

**You only need Python 3.11+. No git clone, no Node install, no admin rights.**

### Windows — one command

```powershell
irm https://raw.githubusercontent.com/Charleschtsoi/dimgaai/main/scripts/install.ps1 | iex
```

### Mac / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/Charleschtsoi/dimgaai/main/scripts/install.sh | bash
```

The installer will:

1. Install the `dimgaai` CLI
2. Download the app from GitHub (no manual clone)
3. Download portable Node + ffmpeg into `.tools/` (no admin)
4. Build the UI on first run (~2–5 min)
5. Open **http://localhost:8000**

### Every day after that

```powershell
dimgaai go       # start
dimgaai stop     # stop
dimgaai doctor   # check status
```

API keys are entered in the browser (**⚙️ API 設定**) — not in the terminal.

---

## Alternative installs

| Method | When to use |
|--------|-------------|
| **Installer script** (above) | **Recommended** — works without git |
| `pip install git+https://github.com/Charleschtsoi/dimgaai.git#subdirectory=backend` then `dimgaai go` | If you prefer pip and have git |
| Clone repo + `.\scripts\dimgaai.ps1 go` | Developers hacking on the code |

> **Phase 2:** `pip install dimgaai` from PyPI (no git URL) — not available yet.

---

## First-time walkthrough

### What you need

| Item | Required? |
|------|-----------|
| Python 3.11+ | Yes — [python.org](https://www.python.org/downloads/) |
| Git clone | **No** |
| Node.js / ffmpeg install | **No** — auto-downloaded |
| Admin rights | **No** |
| 2 API keys | Yes — paste in browser |
| Microphone | Yes |

### Get 2 API keys

| Key | Sign up | Purpose |
|-----|---------|---------|
| **Deepgram** | [console.deepgram.com](https://console.deepgram.com/) | Live Cantonese mic (`zh-HK`) |
| **Google Gemini** *(recommended)* | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Analysis, fact-check, PDF search |

Gemini keys usually start with `AIza...`.

### In the browser

1. **API 設定** → choose **Gemini** preset → paste both keys → **儲存** (confirm **2/2**)
2. *(Optional)* Upload PDFs in **上傳參考文件**
3. **開始錄音** → allow mic → wait for **已連線** → speak
4. **停止錄音** → **匯出報告** (Markdown or PDF)

---

## Command reference

| Command | Description |
|---------|-------------|
| `dimgaai go` | Start app + open browser |
| `dimgaai stop` | Stop server |
| `dimgaai doctor` | Check prerequisites |
| `dimgaai bootstrap --force` | Re-download app from GitHub |
| `dimgaai setup` | API keys in terminal (optional) |

**From a git clone** — same commands via the wrapper:

```powershell
.\scripts\dimgaai.ps1 go
.\scripts\dimgaai.ps1 stop
```

**Install locations**

| Platform | App files | Portable tools |
|----------|-----------|----------------|
| Windows (pip install) | `%LOCALAPPDATA%\dimgaai\app` | `%LOCALAPPDATA%\dimgaai\app\.tools\` |
| Mac/Linux | `~/.local/share/dimgaai/app` | `~/.local/share/dimgaai/app/.tools/` |
| Git clone | Your repo folder | `<repo>\.tools\` |

---

## API keys

**Default:** enter in browser after `dimgaai go` opens.

| Method | How |
|--------|-----|
| Browser | **API 設定** → paste keys → **儲存** |
| Terminal | `dimgaai setup` |
| File | Copy `.env.example` → `.env` in app folder |

```env
DEEPGRAM_API_KEY=your_deepgram_key
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Never commit `.env`.

---

## Why two APIs?

| Job | API |
|-----|-----|
| **Live mic transcript** | Deepgram (`zh-HK`) |
| **Analysis / fact-check / questions** | Gemini *(recommended)*, OpenAI, or Anthropic |

Claude cannot replace Deepgram for live mic. One Google key covers chat + PDF embeddings.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Install Python 3.11+ |
| `dimgaai` not found after install | Close and reopen terminal, or run `python -m dimgaai_cli go` |
| Port 8000 in use | `dimgaai stop` then `dimgaai go` |
| **未連線** when recording | **API 設定** → save both keys → retry |
| No transcript after **已連線** | Wait 3–5 sec; use headset |
| PDF upload error | `dimgaai bootstrap --force` then re-upload |
| Gemini 404 / `gemini-2.0-flash` retired | Set `GEMINI_MODEL=gemini-2.5-flash` in `.env`, or `dimgaai bootstrap --force` |
| Transcript feels slow | Raw text shows first; normalized text updates in place after ~1s |
| Export issues | Hard-refresh browser (Ctrl+Shift+R) |
| winget errors | Ignore — portable tools are used instead |

---

## How it works

```
Mic (webm/opus) → Deepgram nova-2 zh-HK
  → LLM normalizer (書面語) → claim detector
  → RAG fact-check (PDFs) → follow-up questions
```

---

## Features

- Live Cantonese transcription with speaker labels
- PDF upload for glossary + fact-checking
- TRUE / FALSE / UNCERTAIN verdicts
- Follow-up questions on claims or every ~30s
- Export Markdown / PDF
- Mobile-first PWA
- No admin install (portable Node/ffmpeg)

---

## Phase 2 (planned)

| Item | Status |
|------|--------|
| `pip install dimgaai` from **PyPI** | Planned |
| Docker + `docker compose up` | Dockerfile in repo |
| Public web deploy (Railway / VPS) | Planned |
| Pre-built UI in release (skip first-time build) | Planned |

Phase 1 (current): local CLI, BYOK, browser UI at localhost:8000.

---

## For developers

<details>
<summary>Clone and run</summary>

```powershell
git clone https://github.com/Charleschtsoi/dimgaai.git
cd dimgaai
.\scripts\dimgaai.ps1 go
```

</details>

<details>
<summary>All CLI commands</summary>

| Command | Description |
|---------|-------------|
| `go` | Build (if needed) + serve on :8000 |
| `stop` | Stop server |
| `doctor` | Check status |
| `bootstrap` | Download/update app from GitHub |
| `setup` | Terminal API wizard |
| `dev` | Vite dev mode on :5173 |
| `test` | Automated checklist |

Prefix with `.\scripts\dimgaai.ps1` on Windows or `./scripts/dimgaai.sh` on Mac/Linux.

</details>

<details>
<summary>Manual dev</summary>

```powershell
cd backend && python -m uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev   # :5173
```

</details>

<details>
<summary>Project structure</summary>

```
dimgaai/
├── scripts/
│   ├── install.ps1       # one-line installer (Windows)
│   ├── install.sh        # one-line installer (Mac/Linux)
│   └── dimgaai.ps1       # wrapper when using git clone
├── backend/
│   ├── app/              # FastAPI, WebSocket, ASR, RAG
│   └── dimgaai_cli/      # CLI, bootstrap, portable tools
├── frontend/             # React + Vite + Tailwind
└── docker-compose.yml    # Phase 2
```

</details>

## License

MIT
