import sqlite3
import os
import queue
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from utils.logger import logger

class SQLiteStore:
    """
    Manages structured SQLite data using a thread-safe connection pool.
    """
    def __init__(self, db_path: str = "data/jarvis.db", pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialize_pool()
        self._create_schema()

    def _initialize_pool(self):
        """Pre-fill connection pool."""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._pool.put(conn)

    @contextmanager
    def get_connection(self):
        """Context manager to lease a connection from the pool."""
        conn = self._pool.get()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            self._pool.put(conn)

    def _create_schema(self):
        """Initialize the basic schema for user profiles and settings."""
        schema = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            username TEXT PRIMARY KEY,
            email TEXT,
            university TEXT,
            major TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self.get_connection() as conn:
                conn.executescript(schema)
                conn.commit()
            logger.debug("Database schema initialized.")
        except Exception as e:
            logger.error(f"Error creating schema: {e}")

    # --- CRUD for User Profiles ---
    
    def create_user(self, username: str, email: str, university: str, major: str) -> bool:
        query = "INSERT INTO user_profiles (username, email, university, major) VALUES (?, ?, ?, ?)"
        try:
            with self.get_connection() as conn:
                conn.execute(query, (username, email, university, major))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"User {username} already exists.")
            return False
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM user_profiles WHERE username = ?"
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching user {username}: {e}")
            return None

    def update_user_university(self, username: str, university: str) -> bool:
        query = "UPDATE user_profiles SET university = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?"
        try:
            with self.get_connection() as conn:
                conn.execute(query, (university, username))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

    # --- CRUD for Settings ---
    
    def set_setting(self, key: str, value: str) -> bool:
        query = "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)"
        try:
            with self.get_connection() as conn:
                conn.execute(query, (key, value))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving setting {key}: {e}")
            return False

    def get_setting(self, key: str) -> Optional[str]:
        query = "SELECT value FROM settings WHERE key = ?"
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (key,))
                row = cursor.fetchone()
                return row["value"] if row else None
        except Exception as e:
            logger.error(f"Error fetching setting {key}: {e}")
            return None
