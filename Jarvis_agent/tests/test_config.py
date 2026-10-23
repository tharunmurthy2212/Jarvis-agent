from app.core.config import Settings


def test_settings_defaults():
    settings = Settings(
        LLM_API_KEY="test-key",
        LLM_BASE_URL="https://api.test.com/v1",
        LLM_MODEL="test-model",
        APP_PORT=8000
    )
    assert settings.LLM_MODEL == "test-model"
    assert settings.APP_PORT == 8000
    assert settings.ENABLE_MEMORY is True


def test_cors_origins_parsing():
    settings = Settings(
        CORS_ORIGINS="http://localhost:3000, http://127.0.0.1:8000"
    )
    assert isinstance(settings.CORS_ORIGINS, list)
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://127.0.0.1:8000" in settings.CORS_ORIGINS
