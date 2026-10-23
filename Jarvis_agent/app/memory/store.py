from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any
from app.memory.database import get_db_connection
from app.schemas.api import ChatMessage, SessionSummary, SessionDetail, MemoryItem
from app.core.config import settings
from app.core.logger import logger


class MemoryStore:
    """Repository for managing chat sessions, messages, and long-term memories."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --- SESSION METHODS ---

    def create_session(self, session_id: Optional[str] = None, preview: str = "") -> str:
        sid = session_id or str(uuid.uuid4())
        now = self._now()
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions (id, created_at, updated_at, preview)
                VALUES (?, ?, ?, ?)
                """,
                (sid, now, now, preview[:100])
            )
        return sid

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        if not session_id:
            return self.create_session()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return row["id"]
        return self.create_session(session_id=session_id)

    def list_sessions(self, limit: int = 50) -> List[SessionSummary]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT s.id, s.created_at, s.updated_at, s.preview,
                       COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                SessionSummary(
                    session_id=row["id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    message_count=row["message_count"],
                    preview=row["preview"] or "New conversation"
                )
                for row in rows
            ]

    def get_session_detail(self, session_id: str) -> Optional[SessionDetail]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("SELECT id, created_at, updated_at FROM sessions WHERE id = ?", (session_id,))
            session_row = cursor.fetchone()
            if not session_row:
                return None

            msg_cursor = conn.execute(
                """
                SELECT role, content, tool_call_id, tool_name, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,)
            )
            messages = [
                ChatMessage(
                    role=m["role"],
                    content=m["content"],
                    tool_call_id=m["tool_call_id"],
                    tool_name=m["tool_name"],
                    created_at=m["created_at"]
                )
                for m in msg_cursor.fetchall()
            ]

            return SessionDetail(
                session_id=session_row["id"],
                created_at=session_row["created_at"],
                updated_at=session_row["updated_at"],
                messages=messages
            )

    def delete_session(self, session_id: str) -> bool:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None
    ) -> None:
        now = self._now()
        with get_db_connection(self.db_path) as conn:
            # Check/Update session
            conn.execute(
                """
                INSERT INTO sessions (id, created_at, updated_at, preview)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at,
                   preview = CASE WHEN sessions.preview = '' OR sessions.preview = 'New conversation' THEN ? ELSE sessions.preview END
                """,
                (session_id, now, now, content[:80], content[:80])
            )
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, tool_call_id, tool_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content, tool_call_id, tool_name, now)
            )

    def get_recent_messages(self, session_id: str, limit: int | None = None) -> List[ChatMessage]:
        limit_val = limit or settings.MAX_HISTORY_MESSAGES
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT role, content, tool_call_id, tool_name, created_at
                FROM (
                    SELECT id, role, content, tool_call_id, tool_name, created_at
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                ORDER BY id ASC
                """,
                (session_id, limit_val)
            )
            return [
                ChatMessage(
                    role=row["role"],
                    content=row["content"],
                    tool_call_id=row["tool_call_id"],
                    tool_name=row["tool_name"],
                    created_at=row["created_at"]
                )
                for row in cursor.fetchall()
            ]

    # --- LONG TERM MEMORY METHODS ---

    def add_memory(self, content: str, category: str = "preference") -> MemoryItem:
        mem_id = str(uuid.uuid4())
        now = self._now()
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO memories (id, content, category, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (mem_id, content.strip(), category.lower(), now)
            )
        return MemoryItem(id=mem_id, content=content.strip(), category=category.lower(), created_at=now)

    def list_memories(self, category: Optional[str] = None) -> List[MemoryItem]:
        with get_db_connection(self.db_path) as conn:
            if category:
                cursor = conn.execute(
                    "SELECT id, content, category, created_at FROM memories WHERE category = ? ORDER BY created_at DESC",
                    (category.lower(),)
                )
            else:
                cursor = conn.execute("SELECT id, content, category, created_at FROM memories ORDER BY created_at DESC")
            return [
                MemoryItem(
                    id=row["id"],
                    content=row["content"],
                    category=row["category"],
                    created_at=row["created_at"]
                )
                for row in cursor.fetchall()
            ]

    def delete_memory(self, memory_id: str) -> bool:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def clear_all_memories(self) -> int:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories")
            return cursor.rowcount

    def get_memories_text_context(self) -> str:
        """Returns formatted string of memories for injection into prompt."""
        memories = self.list_memories()
        if not memories:
            return ""
        lines = [f"- [{m.category.upper()}] {m.content}" for m in memories]
        return "\n".join(lines)


# Singleton memory store
memory_store = MemoryStore()
