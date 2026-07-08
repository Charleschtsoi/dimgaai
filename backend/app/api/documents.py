from __future__ import annotations

import asyncio
import json
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.models.session_store import session_store
from app.services.rag_factcheck import RAGFactChecker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])
fact_checker = RAGFactChecker()


@router.post("")
async def upload_documents(
    session_id: str = Form(...),
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    settings = get_settings()
    ctx = session_store.get_or_create(session_id)
    upload_dir = settings.upload_path / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved: list[tuple[str, Path]] = []
    for upload in files:
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        dest = upload_dir / upload.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(upload.file, f)
        saved.append((upload.filename, dest))

    chunk_count = await fact_checker.ingest_pdfs(ctx, saved)
    return {
        "session_id": session_id,
        "documents": len(saved),
        "chunks_indexed": chunk_count,
    }
