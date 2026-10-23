from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'system', 'user', 'assistant', or 'tool'")
    content: str = Field(..., description="Message text content")
    tool_call_id: Optional[str] = Field(None, description="Tool call identifier if role is tool")
    tool_name: Optional[str] = Field(None, description="Name of tool if role is tool")
    created_at: Optional[str] = Field(None, description="ISO timestamp")


class ToolCallResult(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    result: Any
    status: str = "success"  # "success" or "error"
    execution_time_ms: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User query or instruction")
    session_id: Optional[str] = Field(None, description="Conversation session UUID. Created if null.")
    use_memory: bool = Field(True, description="Whether to include conversation history and long-term memory")
    document_ids: List[str] = Field(default_factory=list, description="IDs of uploaded documents to ground answers")
    model_override: Optional[str] = Field(None, description="Optional override for model name")
    temperature_override: Optional[float] = Field(None, ge=0.0, le=2.0, description="Optional temperature override")
    generate_voice: bool = Field(False, description="Whether to synthesize audio response via Fish Audio TTS")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: List[ToolCallResult] = Field(default_factory=list)
    audio_url: Optional[str] = None
    model_used: str
    timestamp: str


class SessionSummary(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    message_count: int
    preview: str


class SessionDetail(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage] = Field(default_factory=list)


class MemoryItem(BaseModel):
    id: str
    content: str
    category: str = "preference"
    created_at: str


class CreateMemoryRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Fact or preference to remember")
    category: str = Field("preference", description="Category: preference, fact, identity, workflow")


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    char_count: int
    chunk_count: int
    uploaded_at: str
    summary: Optional[str] = None


class DocumentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(3, ge=1, le=10)


class DocumentQueryResult(BaseModel):
    document_id: str
    filename: str
    chunk_id: int
    snippet: str
    page: Optional[int] = None
    score: float


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    model_id: Optional[str] = None


class TTSResponse(BaseModel):
    audio_url: str
    model_id: str
    cached: bool = False


class HealthStatus(BaseModel):
    status: str
    app: str
    version: str
    provider: str
    model: str
    memory_enabled: bool
    tools_registered: List[str]
    database_connected: bool
    timestamp: str


class SystemStatsResponse(BaseModel):
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    total_memories: int
    total_sessions: int
    total_documents: int
    connected_llms: List[Dict[str, Any]]
    active_agents: List[Dict[str, Any]]
    system_status: str
