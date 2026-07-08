# dimgaai 點解

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Real-time Cantonese meeting assistant: live transcription, fact-check verdicts, and follow-up questions.

Repo: https://github.com/Charleschtsoi/dimgaai

---

## Before you start — what you need

| Requirement | Required? | Notes |
|-------------|-----------|-------|
| **Python 3.11+** | Yes | [Download Python](https://www.python.org/downloads/). On Windows, tick “Add to PATH” during install if allowed. |
| **Node.js installed** | **No** | First run downloads a portable copy into `.tools/` (no admin). After the UI is built once, only Python is needed. |
| **Admin / IT install rights** | **No** | `dimgaai go` works on locked-down PCs. Ignore winget errors — portable tools are used instead. |
| **Internet** | First run only | Downloads portable Node, ffmpeg, and Python packages (~2–5 min one-time build). |
| **Microphone** | Yes | Browser will ask for permission when you start recording. |
| **API keys** | Yes (2 recommended) | See [API keys](#api-keys-2-minimum) below. Free tiers exist on Deepgram and Google AI Studio. |

### API keys (2 minimum)

Live meetings need **two different services** — one for the microphone, one for reasoning:

| Key | Sign up | Used for |
|-----|---------|----------|
| **Deepgram** | [console.deepgram.com](https://console.deepgram.com/) | Live Cantonese speech-to-text (`zh-HK`) |
| **Google Gemini** *(recommended)* | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Transcript cleanup, claim detection, fact-check, questions |

**Alternative LLM stacks** (still need Deepgram for the mic):

| Stack | Keys needed |
|-------|-------------|
| **Gemini** *(recommended)* | Deepgram + Google (one Google key for chat + PDF embeddings) |
| OpenAI | Deepgram + OpenAI |
| Anthropic | Deepgram + Anthropic + Google or OpenAI (embeddings only) |

> Claude cannot replace Deepgram for live mic transcription. Gemini file/batch audio is not real-time. See [Why two APIs?](#why-two-apis) for details.

**Optional:** [Tavily](https://tavily.com/) for web-search fallback during fact-checking.

---

## Quick start (2 steps)

### Step 1 — Run one command

From the repo root (or `backend\`):

```powershell
.\scripts\dimgaai.ps1 go
```

**Mac/Linux:**

```bash
./scripts/dimgaai.sh go
```

`dimgaai go` will automatically:

1. Create `.env` if missing and install Python dependencies
2. Prompt for API keys (press **Enter** to skip — you can enter them in the browser later)
3. Download **portable Node.js** and **ffmpeg** into `.tools/` if not already present (no installer, no admin)
4. Build the frontend on first run (~2–5 min, internet required once)
5. Free ports 8000 / 5173 if busy
6. Start the app and open **http://localhost:8000**

> **First run vs later runs:** The first `go` needs internet to download tools and build the UI. After that, only Python is required — the app serves a pre-built UI on port **8000** with no system Node install.

### Step 2 — In the browser

1. Open **Settings** (API) if you skipped keys during setup — choose the **Gemini** preset and paste your 2 keys
2. **Upload reference PDFs** before recording (optional but improves accuracy)
3. Tap **Start recording** and allow microphone access

That's it.

---

## Entering or changing API keys

| Method | Command / action |
|--------|------------------|
| CLI wizard | `.\scripts\dimgaai.ps1 setup` |
| Skip wizard, use browser | `.\scripts\dimgaai.ps1 go --skip-keys` then open Settings in the UI |
| `.env` file | Copy `.env.example` → `.env` and fill in keys manually |

Example `.env` (Gemini stack — recommended):

```env
DEEPGRAM_API_KEY=your_deepgram_key
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_key
```

Google AI Studio keys usually start with `AIza...`. Keep keys private — never commit `.env`.

---

## No admin rights? (locked-down PC)

You do **not** need IT to install Node.js or ffmpeg.

1. Run `dimgaai go` once — portable tools land in `.tools/` inside the project folder
2. If winget fails with “Failed when opening source(s)”, **ignore it** — portable download continues automatically
3. After the first build, run `dimgaai go` anytime with **Python only**
4. Check status: `.\scripts\dimgaai.ps1 doctor` (hints do not block `go`)

**Troubleshooting**

| Problem | Fix |
|---------|-----|
| `python` not found | Use full path, e.g. `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`, or install Python 3.11+ |
| Port 8000 in use | `.\scripts\dimgaai.ps1 stop` then retry `go` |
| ffmpeg missing (mic) | `go` downloads portable ffmpeg; or ask IT — mic will not work without it |
| Build failed | Check internet, delete `frontend\node_modules`, run `go` again |
| Keys deleted from `.env` | Run `setup` or re-enter in browser Settings |

---

## Why two APIs?

Live Cantonese meetings need **two different jobs**:

| Job | API | Why not one LLM only? |
|-----|-----|------------------------|
| **Microphone transcript** | Deepgram (`zh-HK`) | Specialized streaming ASR with diarization |
| **Analysis / fact-check / questions** | One LLM (Gemini, OpenAI, or Anthropic) | Reasoning over text |

Claude has no speech-to-text. Gemini batch/file audio is not real-time. A Gemini-only transcript path would require the Gemini Live API (future work, not in phase 1).

---

## CLI commands

| Command | Description |
|---------|-------------|
| `dimgaai go` | **Recommended** — setup, build, and start in one flow |
| `dimgaai setup` | Interactive API key wizard only |
| `dimgaai init` | Create `.env` + pip install only |
| `dimgaai doctor` | Check status (hints don't block `go`) |
| `dimgaai dev` | Dev mode on port 5173 (needs npm) |
| `dimgaai start` | Production server on port 8000 |
| `dimgaai stop` | Stop processes + free ports |
| `dimgaai test` | Run automated checklist |
| `dimgaai share` | Public HTTPS URL via Cloudflare Tunnel |

**Windows:** `.\scripts\dimgaai.ps1 <command>` from repo root or `backend\`

**Mac/Linux:** `./scripts/dimgaai.sh <command>`

---

## Using the app

1. Run `dimgaai go` (or open a deployed URL in phase 2)
2. Upload reference PDFs **before** recording
3. Start recording and allow microphone access
4. View live transcript (raw ASR + corrected text) and verdict cards
5. Export Markdown / PDF when done

---

## Transcript pipeline (Cantonese accuracy)

Spoken Cantonese is handled in layers — not a single translation step:

```
Mic (webm) → ffmpeg (PCM 16 kHz) → Deepgram nova-2 zh-HK
  → segment batching → ASR-aware LLM normalizer (書面語)
  → claim detector (raw + corrected + context)
  → RAG fact-check → follow-up questions
```

**Tips for better transcripts:**

| Tip | Why |
|-----|-----|
| Upload PDFs **before** recording | Extracts a glossary; boosts Deepgram keywords for domain terms |
| Use a headset in a quiet room | Biggest real-world ASR improvement |
| Speak in full phrases | Batcher + `utterance_end_ms` produce better finals |
| Check `raw_text` vs corrected `text` in UI | Numbers/names may be clearer in raw ASR |

---

## Phase 2 (planned): Docker + public web deploy

- `docker compose up --build` — single container on port 8000
- Railway / Northflank / VPS hosting
- See `Dockerfile` and `docker-compose.yml` (already in repo)

---

## Manual dev (without CLI)

```powershell
# Terminal 1
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Verify

```powershell
.\scripts\dimgaai.ps1 test
```

## Features

- MediaRecorder webm → Deepgram zh-HK streaming ASR with diarization
- PDF glossary extraction → Deepgram keyword boosting
- Post-ASR Traditional Chinese normalization (context + glossary aware)
- LLM claim detection (Cantonese + English code-mixing, dual raw/corrected input)
- RAG fact-check (TRUE / FALSE / UNCERTAIN) with optional Tavily fallback
- Follow-up questions every ~30s or on claim detection
- LLM providers: **OpenAI**, **Anthropic**, or **Google Gemini** (BYOK — stack presets in Settings)
- Export Markdown / PDF with duration, participants, claim count
- Mobile-first UI, PWA, WebSocket auto-reconnect
- Portable Node/ffmpeg for PCs without admin rights

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/session/{id}/configure` | BYOK keys |
| POST | `/documents` | Upload PDFs |
| GET | `/export/{id}?format=md\|pdf` | Export report |
| WS | `/ws/meeting/{id}` | Audio + events |

## Project structure

```
meeting-support/
├── backend/
│   ├── app/              # FastAPI, WebSocket, ASR, RAG, export
│   ├── dimgaai_cli/      # Local CLI (go, setup, doctor, portable tools)
│   └── scripts/          # demo_checklist.py, launcher scripts
├── frontend/             # React + Vite + Tailwind
├── scripts/              # dimgaai.ps1 / .bat / .sh wrappers
├── .tools/               # Portable Node + ffmpeg (auto-created, gitignored)
├── Dockerfile            # Phase 2 single-unit deploy
└── docker-compose.yml
```

## License

MIT
