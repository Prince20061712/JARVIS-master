"""Pytest configuration and fixtures for Flashcard System tests."""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from flashcard_system.config import Settings, setup_logging


@pytest.fixture(scope="session")
def settings():
    """Provide application settings for tests."""
    return Settings(
        debug=True,
        db_url="sqlite:///:memory:",
        log_level="DEBUG"
    )


@pytest.fixture(scope="session")
def test_db_engine(settings):
    """Create test database engine."""
    engine = create_engine(settings.db_url)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Provide test database session."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="session")
def setup_test_logging(settings):
    """Setup logging for tests."""
    logger = setup_logging(
        log_level=settings.log_level,
        log_dir="./tests/logs",
        app_name="jarvis_flashcard_test"
    )
    return logger


@pytest.fixture
def test_cache_dir(tmp_path):
    """Provide temporary directory for cache testing."""
    return tmp_path / "cache"


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
