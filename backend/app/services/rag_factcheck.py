from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.models.events import SourcePassage, Verdict, VerdictResult
from app.models.session_store import SessionContext
from app.services.llm_provider import get_chat_model, get_embeddings
from app.services.web_search import WebSearchService

logger = logging.getLogger(__name__)


class RAGFactChecker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.web_search = WebSearchService()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
        )

    def _collection_name(self, session_id: str) -> str:
        return f"session_{session_id.replace('-', '_')}"

    def _get_client(self) -> chromadb.PersistentClient:
        self.settings.chroma_path.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(self.settings.chroma_path))

    async def ingest_pdfs(
        self, ctx: SessionContext, files: list[tuple[str, Path]]
    ) -> int:
        if not files:
            return 0

        embeddings = get_embeddings(ctx)
        client = self._get_client()
        collection = client.get_or_create_collection(
            name=self._collection_name(ctx.session_id),
            metadata={"hnsw:space": "cosine"},
        )

        total_chunks = 0
        for filename, path in files:
            loader = PyPDFLoader(str(path))
            docs = loader.load()
            chunks = self._splitter.split_documents(docs)
            if not chunks:
                continue

            texts = [c.page_content for c in chunks]
            vectors = await embeddings.aembed_documents(texts)

            ids = []
            metadatas = []
            for i, chunk in enumerate(chunks):
                ids.append(f"{filename}_{i}")
                metadatas.append(
                    {
                        "filename": filename,
                        "page": chunk.metadata.get("page", 0),
                    }
                )

            collection.add(
                ids=ids,
                embeddings=vectors,
                documents=texts,
                metadatas=metadatas,
            )
            total_chunks += len(chunks)

        ctx.state.document_count = len(files)
        return total_chunks

    async def verify(self, ctx: SessionContext, claim_text: str) -> VerdictResult:
        started = time.perf_counter()
        passages = await self._retrieve(ctx, claim_text)
        used_web = False

        max_score = max((p.score for p in passages), default=0.0)
        if max_score < self.settings.rag_similarity_threshold:
            tavily_key = ctx.resolve_tavily_key()
            if tavily_key:
                web_passages = await self.web_search.search(claim_text, tavily_key)
                if web_passages:
                    passages.extend(web_passages)
                    used_web = True

        verdict_data = await self._synthesize_verdict(ctx, claim_text, passages)
        latency_ms = int((time.perf_counter() - started) * 1000)

        return VerdictResult(
            claim=claim_text,
            verdict=Verdict(verdict_data.get("verdict", "UNCERTAIN")),
            confidence=float(verdict_data.get("confidence", 0.0)),
            rationale=verdict_data.get("rationale", ""),
            sources=passages[:4],
            latency_ms=latency_ms,
            used_web_search=used_web,
        )

    async def _retrieve(
        self, ctx: SessionContext, claim_text: str
    ) -> list[SourcePassage]:
        try:
            embeddings = get_embeddings(ctx)
            query_vector = await embeddings.aembed_query(claim_text)
        except Exception:
            logger.exception("Embedding query failed")
            return []

        client = self._get_client()
        try:
            collection = client.get_collection(self._collection_name(ctx.session_id))
        except Exception:
            return []

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=4,
            include=["documents", "metadatas", "distances"],
        )

        passages: list[SourcePassage] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            score = max(0.0, 1.0 - float(dist))
            passages.append(
                SourcePassage(
                    text=doc,
                    filename=(meta or {}).get("filename", ""),
                    page=(meta or {}).get("page"),
                    score=score,
                )
            )
        return passages

    async def _synthesize_verdict(
        self,
        ctx: SessionContext,
        claim_text: str,
        passages: list[SourcePassage],
    ) -> dict:
        context = "\n\n".join(
            f"[{p.filename} p.{p.page}] {p.text}" for p in passages
        ) or "No reference passages available."

        system = """You are a fact-checker for Cantonese/Traditional Chinese meetings.
Given a claim and reference passages, return ONLY JSON:
{"verdict":"TRUE|FALSE|UNCERTAIN","confidence":0.0-1.0,"rationale":"brief explanation in Traditional Chinese","source_quote":"best supporting quote or empty"}

Use UNCERTAIN when evidence is insufficient or ambiguous."""

        user = f"Claim:\n{claim_text}\n\nReference passages:\n{context}"

        try:
            llm = get_chat_model(ctx)
            response = await llm.ainvoke(
                [SystemMessage(content=system), HumanMessage(content=user)]
            )
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            text = str(content).strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            return json.loads(text)
        except Exception:
            logger.exception("Verdict synthesis failed")
            return {
                "verdict": "UNCERTAIN",
                "confidence": 0.0,
                "rationale": "無法完成核實。",
                "source_quote": "",
            }
