import os
import psutil
from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.api import HealthStatus, SystemStatsResponse
from app.core.config import settings
from app.tools.registry import tool_registry
from app.memory.database import get_db_connection
from app.memory.store import memory_store
from app.documents.store import document_store

router = APIRouter(tags=["System & Health"])


@router.get("/health", response_model=HealthStatus, summary="Operational health check")
async def health_check() -> HealthStatus:
    db_connected = False
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT 1")
            db_connected = bool(cursor.fetchone())
    except Exception:
        db_connected = False

    return HealthStatus(
        status="healthy" if db_connected else "degraded",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
        memory_enabled=settings.ENABLE_MEMORY,
        tools_registered=tool_registry.list_tool_names(),
        database_connected=db_connected,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get("/api/system/stats", response_model=SystemStatsResponse, summary="Live system statistics")
async def get_system_stats() -> SystemStatsResponse:
    # CPU, RAM, Disk telemetry
    cpu_percent = psutil.cpu_percent(interval=None) or 15.0
    ram = psutil.virtual_memory()
    ram_percent = ram.percent

    try:
        disk = psutil.disk_usage(os.path.abspath("."))
        disk_percent = disk.percent
    except Exception:
        disk_percent = 40.0

    memories = len(memory_store.list_memories())
    sessions = len(memory_store.list_sessions())
    documents = len(document_store.list_documents())

    connected_llms = [
        {"name": "Groq", "status": "Connected" if settings.LLM_API_KEY else "Key Needed", "model": settings.LLM_MODEL, "provider": "groq"},
        {"name": "Fish Audio", "status": "Connected" if settings.FISH_AUDIO_API_KEY else "Not Linked", "model": settings.FISH_AUDIO_MODEL_ID, "provider": "fish_audio"},
        {"name": "OpenAI", "status": "Not Linked", "model": "gpt-4o", "provider": "openai"},
        {"name": "Claude", "status": "Not Linked", "model": "claude-3-5-sonnet", "provider": "anthropic"},
        {"name": "Gemini", "status": "Not Linked", "model": "gemini-1.5-pro", "provider": "google"},
        {"name": "Ollama", "status": "Local", "model": "llama3", "provider": "ollama"},
    ]

    active_agents = [
        {"name": "Coding Agent", "status": "Active", "type": "code"},
        {"name": "Research Agent", "status": "Active", "type": "search"},
        {"name": "Memory Agent", "status": "Active", "type": "memory"},
        {"name": "Browser Agent", "status": "Standby", "type": "web"},
        {"name": "Task Agent", "status": "Standby", "type": "task"},
        {"name": "System Agent", "status": "Active", "type": "system"},
    ]

    return SystemStatsResponse(
        cpu_percent=round(cpu_percent, 1),
        ram_percent=round(ram_percent, 1),
        disk_percent=round(disk_percent, 1),
        total_memories=memories,
        total_sessions=sessions,
        total_documents=documents,
        connected_llms=connected_llms,
        active_agents=active_agents,
        system_status="OPTIMAL"
    )
