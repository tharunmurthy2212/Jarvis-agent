from app.llm.base import BaseLLMProvider
from app.llm.openai_adapter import OpenAICompatibleProvider
from app.core.config import settings


def get_llm_provider() -> BaseLLMProvider:
    """Return configured LLM provider instance."""
    return OpenAICompatibleProvider(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        default_model=settings.LLM_MODEL,
        timeout=settings.LLM_REQUEST_TIMEOUT
    )
