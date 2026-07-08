# Cantonese Meeting Support Agent

Real-time Cantonese meeting assistant with live transcription, claim detection, RAG fact-checking, and Traditional Chinese follow-up questions.

## Stack

- **Backend:** FastAPI, Deepgram (zh-HK), LangChain, Chroma
- **Frontend:** React, Vite, TypeScript, Tailwind CSS
- **LLM:** OpenAI or Anthropic (BYOK)

## Features

- WebSocket mic capture → Deepgram streaming ASR (`zh-HK`)
- Live transcript with speaker diarization
- LLM claim detection (Cantonese + English code-mixing)
- RAG fact-check against uploaded PDFs (TRUE / FALSE / UNCERTAIN)
- Optional Tavily web search fallback
- Traditional Chinese follow-up questions
- Export meeting summary as Markdown or PDF

## Quick start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys, or use the in-app BYOK settings panel
```

Required keys:
- `DEEPGRAM_API_KEY` — live transcription
- `OPENAI_API_KEY` — LLM + embeddings (or Anthropic + OpenAI for embeddings)

Optional:
- `TAVILY_API_KEY` — web search fallback

### 2. Run backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Run frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Docker

```bash
docker compose up --build
```

## Usage

1. Click **API 設定 (BYOK)** and enter your keys (or set them in `.env`)
2. Upload one or more reference PDFs
3. Click **開始錄音** and speak in Cantonese (code-mixing supported)
4. View live transcript (left) and verdicts + questions (right)
5. Export Markdown or PDF when done

## Demo acceptance criteria

Run the demo script after starting the backend:

```bash
cd backend
python scripts/demo_checklist.py
```

Manual demo:
1. Upload reference PDFs containing verifiable facts
2. Speak or play ~2 min Cantonese audio with at least one factual claim
3. Verify: live transcript, ≥1 verdict within 5s, ≥1 TC question, no crash on code-mix
4. Export report

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/session/{id}/configure` | Configure BYOK keys |
| POST | `/documents` | Upload PDFs (multipart) |
| GET | `/export/{id}?format=md\|pdf` | Export meeting report |
| WS | `/ws/meeting/{id}` | Audio stream + events |

## WebSocket events (server → client)

```json
{"type":"transcript","speaker":0,"text":"...","is_final":true}
{"type":"verdict","claim":"...","verdict":"TRUE","confidence":0.9,"rationale":"...","sources":[],"latency_ms":2800}
{"type":"questions","segment":"...","questions":["..."]}
```

## Project structure

```
meeting-support/
├── backend/app/          # FastAPI application
├── frontend/src/         # React UI
├── docker-compose.yml
└── .env.example
```
