import os
import logging
import asyncio
from typing import List, Dict, Optional, Any

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

logger = logging.getLogger("LLMClient")

class LLMClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMClient, cls).__new__(cls)
            cls._instance.openai_client = None
            cls._instance.anthropic_client = None
            cls._instance.provider = "openai" # Default
        return cls._instance

    def __init__(self):
        # Initialize clients if keys exist
        if not self.openai_client and AsyncOpenAI and os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not self.anthropic_client and AsyncAnthropic and os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def chat(self, messages: List[Dict[str, str]], model: str = None, temperature: float = 0.7) -> str:
        """
        Unified chat completion method.
        """
        if self.provider == "openai" and self.openai_client:
            return await self._chat_openai(messages, model or "gpt-3.5-turbo", temperature)
        elif self.provider == "anthropic" and self.anthropic_client:
            return await self._chat_anthropic(messages, model or "claude-3-opus-20240229", temperature)
        else:
            logger.warning("No valid LLM provider configured or keys missing. Returning mock response.")
            return self._mock_response(messages)

    async def _chat_openai(self, messages, model, temperature):
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return f"Error communicating with AI: {e}"

    async def _chat_anthropic(self, messages, model, temperature):
        # Anthropic requires system prompt separate from messages usually, 
        # but for simplicity we'll pass messages. 
        # (Adapting schema might be needed for robust impl)
        try:
            # Simple conversion for standard messages
            system = next((m["content"] for m in messages if m["role"] == "system"), "")
            user_msgs = [m for m in messages if m["role"] != "system"]
            
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=1024,
                system=system,
                messages=user_msgs,
                temperature=temperature
            )
            return response.content[0].text
        except Exception as e:
             logger.error(f"Anthropic error: {e}")
             return f"Error communicating with AI: {e}"

    def _mock_response(self, messages):
        last_user_msg = messages[-1]['content']
        return f"[MOCK AI] I received your message: '{last_user_msg}'. API keys are missing."
