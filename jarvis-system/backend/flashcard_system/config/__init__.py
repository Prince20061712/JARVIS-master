"""Configuration module for Flashcard System."""

from .settings import Settings
from .logging_config import setup_logging

__all__ = ['Settings', 'setup_logging']
