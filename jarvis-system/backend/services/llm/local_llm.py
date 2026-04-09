"""
Local LLM Integration for Offline Operation.
"""

import asyncio
import os
from typing import Optional, Dict, Any, AsyncGenerator, List
import json
import aiohttp
from dataclasses import dataclass
from utils.logger import logger

@dataclass
class LLMConfig:
    model_name: str = "phi3"
    api_base: str = "http://localhost:11434"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class LocalLLM:
    """
    Interface for local LLM (Ollama/LlamaCPP)
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.session = None
        self.model_loaded = False
        
    async def initialize(self):
        """Initialize connection to LLM server"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
        try:
            # Check if model is available
            async with self.session.get(f"{self.config.api_base}/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    self.model_loaded = any(
                        m['name'].split(':')[0] == self.config.model_name.split(':')[0] 
                        for m in models.get('models', [])
                    )
            
            if not self.model_loaded:
                logger.warning(f"Model {self.config.model_name} not found locally. Attempting to pull...")
                await self._pull_model()
        except Exception as e:
            logger.error(f"Failed to connect to local LLM server at {self.config.api_base}: {e}")
    
    async def _pull_model(self):
        """Pull model if not available"""
        try:
            async with self.session.post(
                f"{self.config.api_base}/api/pull",
                json={"name": self.config.model_name}
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            progress = json.loads(line)
                            logger.info(f"Pulling model: {progress.get('status', 'processing')}")
                    self.model_loaded = True
        except Exception as e:
            logger.error(f"Error pulling model {self.config.model_name}: {e}")
    
    async def generate(self, 
                      prompt: str, 
                      stream: bool = False,
                      **kwargs) -> AsyncGenerator[str, None] | str:
        """Generate text from prompt"""
        if not self.session: await self.initialize()
        
        payload = {
            "model": self.config.model_name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": kwargs.get('temperature', self.config.temperature),
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens),
                "top_p": kwargs.get('top_p', self.config.top_p),
                "frequency_penalty": kwargs.get('frequency_penalty', 
                                               self.config.frequency_penalty),
                "presence_penalty": kwargs.get('presence_penalty', 
                                              self.config.presence_penalty)
            }
        }
        
        async with self.session.post(
            f"{self.config.api_base}/api/generate",
            json=payload
        ) as response:
            if stream:
                async def stream_gen():
                    async for line in response.content:
                        if line:
                            chunk = json.loads(line)
                            yield chunk.get('response', '')
                return stream_gen()
            else:
                result = await response.json()
                return result.get('response', '')
    
    async def chat(self, 
                  messages: List[Dict[str, str]],
                  stream: bool = False,
                  **kwargs) -> AsyncGenerator[str, None] | str:
        """Chat completion"""
        # Format messages for Ollama API style if they support /api/chat
        # Or fallback to formatted prompt
        if not self.session: await self.initialize()
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": stream,
        }
        
        async with self.session.post(
            f"{self.config.api_base}/api/chat",
            json=payload
        ) as response:
            if stream:
                async def stream_gen():
                    async for line in response.content:
                        if line:
                            chunk = json.loads(line)
                            yield chunk.get('message', {}).get('content', '')
                return stream_gen()
            else:
                result = await response.json()
                return result.get('message', {}).get('content', '')

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None


async def local_generate(prompt: str) -> AsyncGenerator[str, None]:
    """Stream a completion from the local Ollama model."""
    configured_model = os.getenv("LLM_MODEL", os.getenv("OLLAMA_MODEL", "phi3"))
    api_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    candidate_models = [configured_model]
    if configured_model != "mistral":
        candidate_models.append("mistral")

    last_error: Exception | None = None

    for model_name in candidate_models:
        llm = LocalLLM(LLMConfig(model_name=model_name, api_base=api_base))
        try:
            stream = await llm.generate(prompt, stream=True)
            async for chunk in stream:
                if chunk:
                    yield chunk
            return
        except Exception as exc:
            last_error = exc
            logger.warning(f"Local model {model_name} failed: {exc}")
        finally:
            await llm.close()

    if last_error is not None:
        logger.error(f"Local LLM streaming error: {last_error}")
        yield f"Local model error: {last_error}"
