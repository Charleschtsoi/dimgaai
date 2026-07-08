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

## Step-by-step guide (first time)

Follow these steps in order. Total setup time: ~10 minutes (mostly first-run download).

### Step 1 — Get your 2 API keys

You need two free-tier accounts:

| # | Service | Where to sign up | What to copy |
|---|---------|------------------|--------------|
| 1 | **Deepgram** | [console.deepgram.com](https://console.deepgram.com/) | API key (for live Cantonese mic) |
| 2 | **Google Gemini** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | API key starting with `AIza...` |

Keep both keys handy — you will paste them in the browser in Step 4.

> **Why two keys?** Deepgram handles live microphone transcription; Gemini handles analysis, fact-checking, and follow-up questions. See [Why two APIs?](#why-two-apis).

---

### Step 2 — Install Python (if needed)

1. Download **Python 3.11 or 3.12** from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. If your IT policy allows, tick **“Add python.exe to PATH”**
4. Verify in PowerShell:
   ```powershell
   python --version
   ```
   If `python` is not found, use the full path (common on locked-down PCs):
   ```
   %LOCALAPPDATA%\Programs\Python\Python312\python.exe
   ```

You do **not** need Node.js installed separately — the app downloads a portable copy on first run.

---

### Step 3 — Start the app

Open PowerShell, go to the project folder, and run:

```powershell
cd "D:\path\to\meeting-support"
.\scripts\dimgaai.ps1 go
```

**What happens:**

| Phase | What you see | Time |
|-------|----------------|------|
| First run | Downloads portable tools + builds UI | ~2–5 min |
| Every run | Starts server, opens browser | ~10 sec |

Your browser should open **http://localhost:8000** automatically.

**If winget shows an error** — ignore it. Portable tools download into `.tools/` without admin rights.

**To stop the app later:**
```powershell
.\scripts\dimgaai.ps1 stop
```

---

### Step 4 — Enter API keys in the browser

1. On first visit, an **onboarding overlay** appears
2. Tap **「開啟設定」** (Open Settings), or click **⚙️ API 設定** in the top bar
3. Under **方案**, keep **Google Gemini（推薦 — 2 把金鑰）** selected
4. Paste your keys:
   - **Deepgram API Key** → from Step 1
   - **Google Gemini API Key** → from Step 1
5. Tap **「儲存」** (Save)
6. Confirm the banner shows **已設定 2/2 把必需金鑰**

Keys are stored for this session only — they are not sent to our servers.

---

### Step 5 — (Optional) Upload reference PDFs

Before recording, you can upload PDFs to improve accuracy:

1. Drag PDF files into **「上傳參考文件」** at the top
2. Wait until the header shows **「N 份參考文件已索引」**

This helps with domain-specific terms and fact-checking against your documents.

---

### Step 6 — Start recording

1. Click the green **「🎙️ 開始錄音」** button
2. When the browser asks, click **Allow** for microphone access
3. Wait until the status badge turns green: **「已連線」** (Connected)
4. Speak in Cantonese (or Cantonese mixed with English)

**Within a few seconds**, your speech should appear in the **「即時轉錄」** panel on the left.

| Status badge | Meaning |
|--------------|---------|
| 未連線 | Not recording / not connected |
| 連線中… | Connecting to transcription service |
| **已連線** | Ready — speak now |
| 連線錯誤 | Something failed — see red message below button |

---

### Step 7 — Use the results

While recording:

| Panel | What it shows |
|-------|----------------|
| **即時轉錄** (left) | Live Cantonese transcript with speaker labels |
| **核查結果 & 追問** (right) | Fact-check verdicts (TRUE / FALSE / UNCERTAIN) and follow-up questions |

When a factual claim is detected, the app checks it against your uploaded PDFs (if any).

---

### Step 8 — Stop and export

1. Click **「⏹ 停止錄音」** when finished
2. Click **「匯出報告」** to download Markdown or PDF
3. To run another meeting: `.\scripts\dimgaai.ps1 go` again

---

## Quick reference (returning users)

```powershell
.\scripts\dimgaai.ps1 go      # start app + open browser
.\scripts\dimgaai.ps1 stop     # stop server
.\scripts\dimgaai.ps1 doctor   # check status
```

1. Open http://localhost:8000
2. Enter keys in **API 設定** if not already saved
3. **開始錄音** → wait for **已連線** → speak
4. **停止錄音** → **匯出報告**

---

## Entering or changing API keys

| Method | Command / action |
|--------|------------------|
| **Browser (default)** | Run `go` — onboarding opens Settings to paste keys |
| CLI wizard (optional) | `.\scripts\dimgaai.ps1 setup` |
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
| Status stays **未連線** | Open **API 設定**, paste both keys, tap **儲存**, then retry recording |
| **已連線** but no transcript | Speak louder; use a headset; wait 3–5 seconds after connecting |
| Red error under record button | Read the message — usually missing API key or invalid key |
| Build failed | Check internet, delete `frontend\node_modules`, run `go` again |
| Keys deleted from `.env` | Re-enter in browser **API 設定** (no terminal prompt needed) |
| Export opens API settings again | Fixed — export downloads in-place; refresh page after update if needed |
| Deepgram timeout error | Restart with `stop` then `go` — latest version sends WebM directly to Deepgram |

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
| `dimgaai setup` | Optional CLI API key wizard (browser BYOK is default) |
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
Mic (webm/opus) → Deepgram nova-2 zh-HK (direct stream)
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

- MediaRecorder webm/opus → Deepgram zh-HK streaming ASR (direct, no ffmpeg on live path)
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
