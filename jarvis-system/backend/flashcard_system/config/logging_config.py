"""Logging configuration for the application."""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    app_name: str = "jarvis_flashcard"
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        app_name: Application name for logging
    
    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # File Handler
    log_file = os.path.join(log_dir, f"{app_name}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
