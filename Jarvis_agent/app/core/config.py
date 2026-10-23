from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application settings
    APP_NAME: str = "JARVIS AI Assistant"
    APP_VERSION: str = "3.0.0"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = False

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000", "*"]

    # Storage paths
    DATABASE_PATH: str = "data/jarvis.db"
    DOCUMENTS_DIR: str = "data/documents"
    AUDIO_CACHE_DIR: str = "data/audio"

    # LLM Provider configuration (OpenAI compatible)
    LLM_PROVIDER: str = "groq"  # groq, openai, openrouter, ollama, custom
    LLM_API_KEY: str = "enter your api key"  # enter your api key
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.5
    LLM_MAX_TOKENS: int = 4096
    LLM_REQUEST_TIMEOUT: float = 60.0

    # Memory and Engine settings
    ENABLE_MEMORY: bool = True
    MAX_HISTORY_MESSAGES: int = 20
    MAX_TOOL_ITERATIONS: int = 5
    CONTEXT_TOKEN_BUDGET: int = 12000

    # Web search settings
    SEARCH_PROVIDER: str = "duckduckgo"  # duckduckgo, tavily, none
    SEARCH_API_KEY: str = "enter your api key"  # enter your api key
    SEARCH_MAX_RESULTS: int = 5

    # TTS settings (ElevenLabs & Fish Audio)
    TTS_PROVIDER: str = "elevenlabs"  # elevenlabs, fish_audio, none
    ELEVENLABS_API_KEY: str = "enter your api key"  # enter your api key
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"  # George (British JARVIS voice)
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    FISH_AUDIO_API_KEY: str = "enter your api key"  # enter your api key
    FISH_AUDIO_MODEL_ID: str = "05b36da8574341d0803391491850db20"

    # Document upload limits
    MAX_FILE_SIZE_MB: int = 25
    MAX_EXTRACT_CHARS: int = 250000
    DOCUMENT_CHUNK_SIZE: int = 1200
    DOCUMENT_CHUNK_OVERLAP: int = 200

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    def ensure_directories(self) -> None:
        """Create necessary data directories if they do not exist."""
        for p in [Path(self.DATABASE_PATH).parent, Path(self.DOCUMENTS_DIR), Path(self.AUDIO_CACHE_DIR)]:
            p.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()
