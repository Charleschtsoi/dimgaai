# dimgaai 點解

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Real-time Cantonese meeting assistant: live transcription, fact-check verdicts, and follow-up questions.

Repo: https://github.com/Charleschtsoi/dimgaai

## Quick start (local CLI — Phase 1)

No Docker or cloud hosting required for local use.

### 1. One-time setup

```powershell
cd meeting-support
.\scripts\dimgaai.ps1 init
```

Edit `.env` and add your API keys (or use BYOK in the browser later):

```
DEEPGRAM_API_KEY=...
OPENAI_API_KEY=...
```

Install [ffmpeg](https://ffmpeg.org/) for mic transcription (`choco install ffmpeg` on Windows).

Install [Node.js](https://nodejs.org/) for the frontend.

### 2. Check prerequisites

```powershell
.\scripts\dimgaai.ps1 doctor
```

### 3. Start the app

```powershell
.\scripts\dimgaai.ps1 dev
```

Opens **http://localhost:5173** — tap **🎙️ 開始錄音** and allow the microphone.

### CLI commands

| Command | Description |
|---------|-------------|
| `dimgaai init` | Create `.env`, install Python deps |
| `dimgaai doctor` | Check Python, ffmpeg, Node, ports, keys |
| `dimgaai dev` | Backend + Vite dev server (port 5173) |
| `dimgaai start` | Build frontend, single server on port 8000 |
| `dimgaai stop` | Stop background processes |
| `dimgaai test` | Run automated checklist |
| `dimgaai share` | Public HTTPS URL via Cloudflare Tunnel (optional) |

**Windows:** `.\scripts\dimgaai.ps1 <command>` or `scripts\dimgaai.bat dev`

**Mac/Linux:** `./scripts/dimgaai.sh dev`

**Global install (optional):**

```bash
cd backend
pip install -r requirements.txt
pip install -e .
dimgaai dev
```

### Optional: share a public demo link

```powershell
# Install cloudflared first
.\scripts\dimgaai.ps1 share
```

Prints a temporary `https://….trycloudflare.com` URL. Your PC must stay on.

---

## For Users

1. Run `dimgaai dev` (or open a deployed URL in phase 2)
2. **Upload reference PDFs before recording** (improves ASR + fact-checking)
3. Tap **🎙️ 開始錄音** and allow microphone access
4. View live transcript (raw ASR + corrected text) and verdict cards
5. Export report when done

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

**What the LLM receives for fact-check / questions:**

- ASR raw text (recover numbers if correction is wrong)
- Corrected Traditional Chinese transcript
- Recent conversation context (last few segments)
- Meeting glossary from uploaded PDFs
- Fact-check verdict (when a claim is detected)

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
- Follow-up questions every ~30s or on claim detection (includes verdict context)
- BYOK API keys via in-app settings
- Export Markdown / PDF with duration, participants, claim count
- Mobile-first UI, PWA, WebSocket auto-reconnect

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
│   ├── dimgaai_cli/      # Local CLI (init, doctor, dev, start, stop)
│   └── scripts/          # demo_checklist.py
├── frontend/             # React + Vite + Tailwind
├── scripts/              # dimgaai.ps1 / .bat / .sh wrappers
├── Dockerfile            # Phase 2 single-unit deploy
└── docker-compose.yml
```

## License

MIT
