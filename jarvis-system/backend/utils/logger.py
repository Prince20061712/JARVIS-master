import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    """
    Singleton Logger class with rotating file handlers and console output.
    Supports log rotation (10MB per file, 5 backups).
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        self.logger = logging.getLogger("JARVIS_Logger")
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "jarvis.log")

        # Formatter for timestamps and log levels
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Default console level
        console_handler.setFormatter(formatter)

        # 2. Rotating File Handler (10MB size, 5 backup files)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def set_level(self, level_name: str):
        """Allow dynamic level changes"""
        level = getattr(logging, level_name.upper(), logging.INFO)
        self.logger.setLevel(level)

    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)

# Global instance to import
logger = Logger()
