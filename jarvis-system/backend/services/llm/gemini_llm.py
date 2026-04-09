"""Gemini streaming provider for complex reasoning."""

from __future__ import annotations

import asyncio
import os
import threading
from typing import AsyncGenerator

from utils.logger import logger


async def gemini_generate(prompt: str) -> AsyncGenerator[str, None]:
    """Stream a completion from Google Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        yield "Gemini API key is not configured."
        return

    try:
        import google.generativeai as genai
    except Exception as exc:
        logger.error(f"Gemini SDK import failed: {exc}")
        yield f"Gemini SDK error: {exc}"
        return

    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _worker() -> None:
        try:
            for chunk in model.generate_content(prompt, stream=True):
                text = getattr(chunk, "text", "") or ""
                if text:
                    asyncio.run_coroutine_threadsafe(queue.put(text), loop)
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(queue.put(f"Gemini streaming error: {exc}"), loop)
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)

    threading.Thread(target=_worker, daemon=True).start()

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk
        await asyncio.sleep(0)
