from __future__ import annotations

import logging

from app.models.events import SourcePassage

logger = logging.getLogger(__name__)


class WebSearchService:
    async def search(self, query: str, api_key: str) -> list[SourcePassage]:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)
            response = client.search(query=query, max_results=3)
            results = response.get("results", [])
            passages: list[SourcePassage] = []
            for item in results:
                content = item.get("content") or item.get("snippet") or ""
                if not content:
                    continue
                passages.append(
                    SourcePassage(
                        text=content,
                        filename=item.get("url", "web"),
                        score=0.5,
                    )
                )
            return passages
        except Exception:
            logger.exception("Web search failed")
            return []
