from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
import os

from core.memory.models import Base
from utils.config_loader import load_config

CONFIG = load_config()

# Determine absolute path to data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "memory.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# specific logic for in-memory or file-based sqlite
connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    poolclass=StaticPool # Needed for SQLite + multiple threads sometimes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Scoped session for thread safety
db_session = scoped_session(SessionLocal)

def init_db():
    import core.memory.models # Import models so Base sees them
    Base.metadata.create_all(bind=engine)

def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
