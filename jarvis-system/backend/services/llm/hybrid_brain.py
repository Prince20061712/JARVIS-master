"""Hybrid orchestration for local, Groq, and Gemini responses."""

from __future__ import annotations

import asyncio
import inspect
import os
from collections.abc import Awaitable, Callable
from typing import AsyncGenerator, Optional

from utils.logger import logger

from .gemini_llm import gemini_generate
from .groq_llm import groq_generate
from .local_llm import local_generate
from .router import COMMAND, FAST, SIMPLE, classify_query

CommandHandler = Callable[[str], Awaitable[str] | str]


class HybridBrain:
    """Route queries to the best provider and keep a simple in-memory cache."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self.local_model = os.getenv("LLM_MODEL", os.getenv("OLLAMA_MODEL", "phi3"))
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    @staticmethod
    def _cache_key(query: str) -> str:
        return " ".join(query.lower().split())

    @staticmethod
    def _stream_text(text: str, chunk_size: int = 32) -> AsyncGenerator[str, None]:
        async def _generator() -> AsyncGenerator[str, None]:
            for index in range(0, len(text), chunk_size):
                yield text[index:index + chunk_size]
                await asyncio.sleep(0)

        return _generator()

    async def _resolve_command(self, query: str, command_handler: Optional[CommandHandler]) -> str:
        if command_handler is None:
            return f"Command received: {query}"

        result = command_handler(query)
        if inspect.isawaitable(result):
            result = await result
        return str(result)

    async def generate_response(
        self,
        query: str,
        command_handler: Optional[CommandHandler] = None,
    ) -> AsyncGenerator[str, None]:
        """Yield a streaming response for the selected provider."""
        cache_key = self._cache_key(query)
        if cache_key in self._cache:
            logger.info("[ROUTER] Cache hit for query")
            async for chunk in self._stream_text(self._cache[cache_key]):
                yield chunk
            return

        route = classify_query(query)
        logger.info(f"[ROUTER] Query classified as {route}")

        if route == COMMAND:
            logger.info("[ROUTER] Using COMMAND handler")
            response_text = await self._resolve_command(query, command_handler)
            self._cache[cache_key] = response_text
            async for chunk in self._stream_text(response_text):
                yield chunk
            return

        if route == SIMPLE:
            logger.info("[ROUTER] Using LOCAL Ollama for simple response")
            provider = local_generate(query)
        elif route == FAST:
            logger.info("[ROUTER] Using GROQ for fast response")
            provider = groq_generate(query)
        else:
            logger.info("[ROUTER] Using GEMINI for complex reasoning")
            provider = gemini_generate(query)

        collected: list[str] = []
        async for chunk in provider:
            if not chunk:
                continue
            collected.append(chunk)
            yield chunk

        response_text = "".join(collected).strip()
        if response_text:
            self._cache[cache_key] = response_text

    def clear_cache(self) -> None:
        self._cache.clear()
