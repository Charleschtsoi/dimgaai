#!/usr/bin/env python3
"""Demo acceptance checklist for Cantonese Meeting Support Agent."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CHECKS = [
    ("FastAPI app", "app.main:app"),
    ("Deepgram stream service", "app.services.deepgram_stream"),
    ("Claim detector", "app.services.claim_detector"),
    ("RAG fact checker", "app.services.rag_factcheck"),
    ("Question generator", "app.services.question_gen"),
    ("Export service", "app.services.export"),
    ("WebSocket handler", "app.ws.meeting"),
]


def main() -> int:
    print("Cantonese Meeting Support Agent — Demo Checklist\n")
    failed = 0

    for label, module in CHECKS:
        try:
            __import__(module.split(":")[0])
            print(f"  [OK] {label}")
        except Exception as exc:
            print(f"  [FAIL] {label}: {exc}")
            failed += 1

    root = Path(__file__).resolve().parents[2]
    frontend_files = [
        root / "frontend" / "src" / "App.tsx",
        root / "frontend" / "src" / "components" / "VerdictSidebar.tsx",
        root / "frontend" / "src" / "hooks" / "useAudioCapture.ts",
    ]
    for path in frontend_files:
        if path.exists():
            print(f"  [OK] Frontend: {path.name}")
        else:
            print(f"  [FAIL] Missing: {path}")
            failed += 1

    print("\nManual acceptance criteria:")
    print("  1. Upload reference PDF(s)")
    print("  2. 2-min Cantonese audio -> live transcript")
    print("  3. >=1 fact-check verdict within 5s of claim")
    print("  4. >=1 Traditional Chinese follow-up question")
    print("  5. Code-mixed Cantonese-English sentence handled without crash")
    print('  6. UI renders on 13" laptop (1280x800)')
    print("  7. Export Markdown/PDF")

    if failed:
        print(f"\n{failed} check(s) failed.")
        return 1
    print("\nAll automated checks passed. Run manual demo with API keys.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
