from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LLMToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[LLMToolCall] = Field(default_factory=list)
    model_used: str
    finish_reason: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class BaseLLMProvider(ABC):
    """Abstract interface for LLM chat completion providers."""

    @abstractmethod
    async def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Execute chat completion request."""
        pass
