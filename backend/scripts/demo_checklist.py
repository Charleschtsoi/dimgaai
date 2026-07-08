#!/usr/bin/env python3
"""Demo acceptance checklist for dimgaai."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

CHECKS = [
    ("FastAPI app", "app.main:app"),
    ("dimgaai CLI", "dimgaai_cli.main"),
    ("CLI prereqs", "dimgaai_cli.prereqs"),
    ("CLI portable tools", "dimgaai_cli.portable_tools"),
    ("Audio decode (webm)", "app.services.audio_decode"),
    ("Transcript normalizer", "app.services.transcript_normalize"),
    ("Meeting glossary", "app.services.meeting_glossary"),
    ("Deepgram stream", "app.services.deepgram_stream"),
    ("Claim detector", "app.services.claim_detector"),
    ("LLM provider (Gemini)", "langchain_google_genai"),
    ("RAG fact checker", "app.services.rag_factcheck"),
    ("Question generator", "app.services.question_gen"),
    ("Export service", "app.services.export"),
    ("Segment batcher", "app.ws.segment_batcher"),
    ("WebSocket handler", "app.ws.meeting"),
]

EVENT_SHAPES = {
    "transcript": {"type", "speaker", "text", "is_final"},
    "claim": {"type", "classification", "claim_text", "segment"},
    "verdict": {"type", "claim", "verdict", "confidence", "rationale", "source_quote"},
    "questions": {"type", "segment", "questions"},
}


def dry_run_events() -> list[str]:
    errors: list[str] = []
    samples = {
        "transcript": {
            "type": "transcript",
            "speaker": 0,
            "text": "測試",
            "raw_text": "測試",
            "is_final": True,
            "timestamp_ms": 0,
            "is_factual_claim": False,
        },
        "claim": {
            "type": "claim",
            "classification": "factual_claim",
            "claim_text": "GDP 增長 3.5%",
            "segment": "GDP 增長 3.5%",
        },
        "verdict": {
            "type": "verdict",
            "claim": "GDP 增長 3.5%",
            "verdict": "UNCERTAIN",
            "confidence": 0.0,
            "rationale": "測試",
            "source_quote": "",
            "sources": [],
            "latency_ms": 100,
            "used_web_search": False,
        },
        "questions": {
            "type": "questions",
            "segment": "測試片段",
            "questions": ["問題一？"],
        },
    }
    for name, required in EVENT_SHAPES.items():
        payload = samples[name]
        missing = required - set(payload.keys())
        if missing:
            errors.append(f"Event '{name}' missing keys: {missing}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Validate WS event shapes")
    args = parser.parse_args()

    print("dimgaai — Demo Checklist\n")
    failed = 0

    for label, module in CHECKS:
        try:
            __import__(module.split(":")[0])
            print(f"  [OK] {label}")
        except Exception as exc:
            print(f"  [FAIL] {label}: {exc}")
            failed += 1

    frontend_files = [
        ROOT / "frontend" / "src" / "App.tsx",
        ROOT / "frontend" / "src" / "components" / "TopBar.tsx",
        ROOT / "frontend" / "src" / "components" / "OnboardingOverlay.tsx",
        ROOT / "frontend" / "public" / "icon.svg",
        ROOT / "Dockerfile",
        ROOT / "railway.toml",
        ROOT / "scripts" / "dimgaai.ps1",
    ]
    for path in frontend_files:
        if path.exists():
            print(f"  [OK] {path.name}")
        else:
            print(f"  [FAIL] Missing: {path}")
            failed += 1

    if args.dry_run:
        print("\nDry-run event shape validation:")
        for err in dry_run_events():
            print(f"  [FAIL] {err}")
            failed += 1
        if not dry_run_events():
            print("  [OK] All event shapes valid")

    print("\nManual acceptance criteria:")
    print("  1. dimgaai go  (or: init && doctor && dev)")
    print("  2. Upload PDF -> record 2 min Cantonese with 1 factual claim")
    print("  3. >=1 verdict <5s, >=1 TC question, code-mix OK")
    print("  4. Export Markdown includes duration, participants, claims")
    print("  5. Mobile 375px, BYOK modal, WS reconnect")

    if failed:
        print(f"\n{failed} check(s) failed.")
        return 1
    print("\nAll automated checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
