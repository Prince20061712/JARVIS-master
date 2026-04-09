"""Groq streaming provider for fast responses."""

from __future__ import annotations

import asyncio
import json
import os
from typing import AsyncGenerator

import aiohttp

from utils.logger import logger

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def groq_generate(prompt: str) -> AsyncGenerator[str, None]:
    """Stream a completion from Groq's OpenAI-compatible API."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        yield "Groq API key is not configured."
        return

    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a fast, concise assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout = aiohttp.ClientTimeout(total=90)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(GROQ_API_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Groq API error {response.status}: {error_text}")
                    yield f"Groq API error {response.status}."
                    return

                async for raw_line in response.content:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue

                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                        await asyncio.sleep(0)
    except Exception as exc:
        logger.error(f"Groq streaming error: {exc}")
        yield f"Groq streaming error: {exc}"
