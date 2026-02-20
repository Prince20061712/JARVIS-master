import os
import yaml
import time
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.logger import logger

class DatabaseConfig(BaseSettings):
    url: str = Field(default="sqlite:///jarvis.db")
    pool_size: int = Field(default=5)

class ServerConfig(BaseSettings):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)

class AppConfig(BaseSettings):
    """
    Main configuration model supporting nested structures.
    Uses Pydantic validation.
    """
    app_name: str = Field(default="JARVIS")
    server: ServerConfig = ServerConfig()
    database: DatabaseConfig = DatabaseConfig()

class ConfigLoader:
    """
    Loads config from YAML and environment variables using Pydantic Settings.
    Supports hot-reloading via file watcher.
    """
    _instance = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "config", "settings.yaml")
            cls._instance._observer = None
            cls._instance.load_config()
            cls._instance.start_watcher()
        return cls._instance

    def load_config(self) -> AppConfig:
        """Loads and validates the configuration."""
        yaml_data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    yaml_data = yaml.safe_load(f) or {}
                logger.debug(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to read config file {self.config_path}: {e}")
        
        try:
            # Pydantic will automatically overlay Env variables over this data if specified
            self._config = AppConfig(**yaml_data)
            logger.info("Configuration validated and loaded successfully.")
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            # If invalid, and we had an old config, we might want to keep the old one
            if self._config is None:
                # Provide a default config so app doesn't immediately crash if starting up
                self._config = AppConfig()
        
        return self._config

    def get_config(self) -> AppConfig:
        if self._config is None:
            self.load_config()
        return self._config

    def start_watcher(self):
        """Starts a background thread to watch for file changes using watchdog."""
        if not os.path.exists(os.path.dirname(self.config_path)):
            logger.warning("Config directory does not exist. Cannot start watcher.")
            return

        class ConfigChangeHandler(FileSystemEventHandler):
            def __init__(self, loader: 'ConfigLoader'):
                self.loader = loader
                self.last_reload = time.time()

            def on_modified(self, event):
                if event.src_path == self.loader.config_path:
                    # Debounce reloads (watchdog sometimes fires multiple events)
                    current_time = time.time()
                    if current_time - self.last_reload > 1.0:
                        logger.info("Config file changed. Hot-reloading...")
                        self.loader.load_config()
                        self.last_reload = current_time

        event_handler = ConfigChangeHandler(self)
        self._observer = Observer()
        self._observer.schedule(event_handler, path=os.path.dirname(self.config_path), recursive=False)
        self._observer.start()
        logger.debug("Config file watcher started.")

    def stop_watcher(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()

# Global instance
config_loader = ConfigLoader()
