import os
import gc
import tempfile
import pytest
from app.memory.database import init_db
from app.memory.store import MemoryStore


@pytest.fixture
def temp_store():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path)
    store = MemoryStore(db_path=db_path)
    yield store
    gc.collect()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


def test_session_lifecycle(temp_store):
    sid = temp_store.create_session(preview="Test conversation")
    assert sid is not None

    # Add messages
    temp_store.add_message(sid, role="user", content="Hello JARVIS")
    temp_store.add_message(sid, role="assistant", content="Greetings! How may I assist you?")

    # Fetch recent messages
    messages = temp_store.get_recent_messages(sid)
    assert len(messages) == 2
    assert messages[0].content == "Hello JARVIS"
    assert messages[1].role == "assistant"

    # Fetch session detail
    detail = temp_store.get_session_detail(sid)
    assert detail is not None
    assert len(detail.messages) == 2

    # Delete session
    assert temp_store.delete_session(sid) is True
    assert temp_store.get_session_detail(sid) is None


def test_long_term_memory(temp_store):
    m1 = temp_store.add_memory(content="User prefers Python for backend development", category="preference")
    m2 = temp_store.add_memory(content="Deploying on Windows 11 host", category="fact")

    memories = temp_store.list_memories()
    assert len(memories) == 2

    # Filter by category
    prefs = temp_store.list_memories(category="preference")
    assert len(prefs) == 1
    assert prefs[0].content == "User prefers Python for backend development"

    # Context formatted string
    context_str = temp_store.get_memories_text_context()
    assert "User prefers Python" in context_str

    # Delete memory
    assert temp_store.delete_memory(m1.id) is True
    assert len(temp_store.list_memories()) == 1

    # Clear all
    temp_store.clear_all_memories()
    assert len(temp_store.list_memories()) == 0
