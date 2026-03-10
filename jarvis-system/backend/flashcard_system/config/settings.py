"""Application settings and configuration management."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_title: str = "JARVIS Flashcard System"
    api_version: str = "3.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database Configuration
    db_url: str = Field(
        default="sqlite:///./jarvis_flashcards.db",
        env="DATABASE_URL"
    )
    
    # LLM Configuration
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="neural-chat", env="OLLAMA_MODEL")
    
    # Vector Store Configuration
    chroma_host: Optional[str] = Field(default=None, env="CHROMA_HOST")
    chroma_port: Optional[int] = Field(default=None, env="CHROMA_PORT")
    vector_db_path: str = Field(
        default="./chroma_db",
        env="VECTOR_DB_PATH"
    )
    
    # Cache Configuration
    cache_dir: str = Field(default="./cache", env="CACHE_DIR")
    embeddings_cache_dir: str = Field(default="./cache/embeddings", env="EMBEDDINGS_CACHE_DIR")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: str = Field(default="./logs", env="LOG_DIR")
    
    # WebSocket Configuration
    websocket_max_connections: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    websocket_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    # Spaced Repetition Configuration
    sm2_ease_factor_min: float = 1.3
    sm2_ease_factor_max: float = 2.5
    sm2_interval_modifier: float = 1.0
    
    # Study Configuration
    daily_card_limit: int = 50
    new_card_limit: int = 20
    review_card_limit: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()
