import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from app.core.config import settings
from app.core.logger import logger


def init_db(db_path: str | None = None) -> None:
    """Initialize database schema with required tables and indexes."""
    path = db_path or settings.DATABASE_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                preview TEXT DEFAULT ''
            );
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_call_id TEXT,
                tool_name TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);")

        # Long-term User Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'preference',
                created_at TEXT NOT NULL
            );
        """)

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                char_count INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                summary TEXT DEFAULT ''
            );
        """)

        # Document Chunks table for retrieval
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                page INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_chunks_doc ON document_chunks(document_id);")

        conn.commit()
        logger.info(f"Database schema initialized successfully at {path}")


@contextmanager
def get_db_connection(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional SQLite connection."""
    path = db_path or settings.DATABASE_PATH
    conn = sqlite3.connect(path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
