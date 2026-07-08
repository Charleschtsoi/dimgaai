# dimgaai 點解

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Real-time Cantonese meeting assistant: live transcription, fact-check verdicts, and follow-up questions.

Repo: https://github.com/Charleschtsoi/dimgaai

---

## Start here (main command)

**The easiest way to run dimgaai on Windows:**

```powershell
cd "D:\path\to\meeting-support"
.\scripts\dimgaai.ps1 go
```

That single command does everything:

1. Installs Python dependencies (first run)
2. Downloads portable Node.js + ffmpeg into `.tools/` if needed (**no admin**)
3. Builds the UI on first run (~2–5 min, needs internet once)
4. Starts the server on **http://localhost:8000**
5. Opens your browser automatically

**Stop the app:**

```powershell
.\scripts\dimgaai.ps1 stop
```

**Check status:**

```powershell
.\scripts\dimgaai.ps1 doctor
```

> Works from the **repo root** or the `backend\` folder.  
> Mac/Linux: `./scripts/dimgaai.sh go`

---

## Full walkthrough (first time)

### 1. Prerequisites

| You need | Required? |
|----------|-----------|
| **Python 3.11+** | Yes — [python.org](https://www.python.org/downloads/) |
| **Node.js installed** | **No** — portable copy auto-downloaded |
| **Admin rights** | **No** — ignore winget errors |
| **2 API keys** | Yes — enter in browser after `go` opens |
| **Microphone** | Yes — browser will ask when you record |

### 2. Get 2 API keys (before or after `go`)

| Key | Sign up | Purpose |
|-----|---------|---------|
| **Deepgram** | [console.deepgram.com](https://console.deepgram.com/) | Live Cantonese mic (`zh-HK`) |
| **Google Gemini** *(recommended)* | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Analysis, fact-check, PDF search |

Gemini keys usually start with `AIza...`. See [Why two APIs?](#why-two-apis) if you wonder why both are needed.

### 3. Run the app

```powershell
.\scripts\dimgaai.ps1 go
```

| Run | What happens | Time |
|-----|----------------|------|
| **First time** | Download tools + build UI + start | ~2–5 min |
| **After that** | Start server + open browser | ~10 sec |

If winget fails — **ignore it**. Portable tools install into `.tools/` without admin.

### 4. Enter API keys in the browser

`go` does **not** ask for keys in the terminal. In the browser:

1. Tap **「開啟設定」** on the onboarding screen, or **⚙️ API 設定** in the top bar
2. Keep **Google Gemini（推薦 — 2 把金鑰）** selected
3. Paste **Deepgram** + **Gemini** keys
4. Tap **「儲存」** — confirm **已設定 2/2**

### 5. (Optional) Upload PDFs

Drag PDFs into **「上傳參考文件」** before recording. Improves domain terms and fact-checking.

### 6. Record a meeting

1. Click **「🎙️ 開始錄音」**
2. Allow microphone access
3. Wait for green **「已連線」**
4. Speak — transcript appears in **「即時轉錄」**

### 7. Stop and export

1. **「⏹ 停止錄音」**
2. **「📥 匯出報告」** → Markdown or PDF

### 8. Next time

```powershell
.\scripts\dimgaai.ps1 go
```

Open http://localhost:8000 → keys are remembered in the browser session → record.

---

## Command cheat sheet (Windows)

All commands use the PowerShell wrapper — **this is the recommended way to run dimgaai:**

| What you want | Command |
|---------------|---------|
| **Start app** (main) | `.\scripts\dimgaai.ps1 go` |
| Stop app | `.\scripts\dimgaai.ps1 stop` |
| Check status | `.\scripts\dimgaai.ps1 doctor` |
| API keys in terminal (optional) | `.\scripts\dimgaai.ps1 setup` |
| Run tests | `.\scripts\dimgaai.ps1 test` |

**Mac/Linux** — replace with `./scripts/dimgaai.sh <command>`.

Advanced users can also run `python -m dimgaai_cli.main go` from `backend\`, but `.\scripts\dimgaai.ps1 go` is easier because it finds Python automatically.

---

## API keys

| Method | How |
|--------|-----|
| **Browser (default)** | `.\scripts\dimgaai.ps1 go` → **API 設定** → paste keys → **儲存** |
| CLI wizard (optional) | `.\scripts\dimgaai.ps1 setup` |
| `.env` file | Copy `.env.example` → `.env` |

```env
DEEPGRAM_API_KEY=your_deepgram_key
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_key
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Never commit `.env` to git.

---

## No admin rights?

You do **not** need IT to install Node.js or ffmpeg.

```powershell
.\scripts\dimgaai.ps1 go
```

Portable tools land in `.tools/` inside the project folder. After the first build, only Python is needed.

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Install Python 3.11+, or use full path: `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` |
| Port 8000 in use | `.\scripts\dimgaai.ps1 stop` then `.\scripts\dimgaai.ps1 go` |
| Status stays **未連線** | **API 設定** → paste both keys → **儲存** → retry |
| **已連線** but no text | Wait 3–5 sec; use headset; speak clearly |
| PDF upload fails | Restart with `stop` + `go` (uses `gemini-embedding-001`) |
| Export asks for keys again | Hard-refresh browser (Ctrl+Shift+R) after `go` |
| Build failed | Delete `frontend\node_modules`, run `.\scripts\dimgaai.ps1 go` again |

---

## Why two APIs?

| Job | API | Why not one LLM? |
|-----|-----|------------------|
| **Live mic transcript** | Deepgram (`zh-HK`) | Streaming ASR + diarization |
| **Analysis / fact-check** | Gemini, OpenAI, or Anthropic | Text reasoning |

Claude has no speech-to-text. Gemini batch audio is not real-time.

| Stack | Keys |
|-------|------|
| **Gemini** *(recommended)* | Deepgram + Google |
| OpenAI | Deepgram + OpenAI |
| Anthropic | Deepgram + Anthropic + embedding key |

---

## How it works

```
Mic (webm/opus) → Deepgram nova-2 zh-HK
  → LLM normalizer (書面語) → claim detector
  → RAG fact-check (PDFs) → follow-up questions
```

**Tips:** upload PDFs first, use a headset, speak in full phrases.

---

## Features

- Live Cantonese transcription with speaker labels
- PDF upload for glossary + fact-checking
- TRUE / FALSE / UNCERTAIN verdicts with source quotes
- Follow-up questions every ~30s or on claims
- Export Markdown / PDF
- Mobile-first PWA UI
- Portable Node/ffmpeg — no admin install needed

---

## For developers

<details>
<summary>All CLI commands</summary>

| Command | Description |
|---------|-------------|
| `.\scripts\dimgaai.ps1 go` | **Start** — build + serve on port 8000 |
| `.\scripts\dimgaai.ps1 stop` | Stop server + free ports |
| `.\scripts\dimgaai.ps1 doctor` | Check prerequisites |
| `.\scripts\dimgaai.ps1 setup` | Terminal API key wizard |
| `.\scripts\dimgaai.ps1 init` | Create `.env` + pip install |
| `.\scripts\dimgaai.ps1 dev` | Dev mode (port 5173) |
| `.\scripts\dimgaai.ps1 test` | Automated checklist |
| `.\scripts\dimgaai.ps1 share` | Public URL via Cloudflare Tunnel |

</details>

<details>
<summary>Manual dev (without script)</summary>

```powershell
# Terminal 1
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm install && npm run dev
```

Open http://localhost:5173

</details>

<details>
<summary>API endpoints</summary>

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/session/{id}/configure` | BYOK keys |
| POST | `/documents` | Upload PDFs |
| GET | `/export/{id}?format=md\|pdf` | Export report |
| WS | `/ws/meeting/{id}` | Audio + events |

</details>

<details>
<summary>Project structure</summary>

```
meeting-support/
├── scripts/dimgaai.ps1   ← main entry point (Windows)
├── backend/
│   ├── app/              # FastAPI, WebSocket, ASR, RAG
│   └── dimgaai_cli/      # CLI + portable tools
├── frontend/             # React + Vite + Tailwind
├── .tools/               # Portable Node + ffmpeg (auto-created)
└── docker-compose.yml    # Phase 2 deploy
```

</details>

## Phase 2 (planned)

Docker + public web deploy — see `Dockerfile` and `docker-compose.yml`.

## License

MIT
