"""Custom domain exceptions for JARVIS assistant."""

class JarvisError(Exception):
    """Base exception for all JARVIS errors."""
    def __init__(self, message: str, safe_message: str | None = None):
        super().__init__(message)
        self.safe_message = safe_message or message


class LLMError(JarvisError):
    """Base exception for LLM provider errors."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when API key or provider authentication fails."""
    def __init__(self, message: str = "Invalid or missing LLM API credentials."):
        super().__init__(message, safe_message="LLM authentication failed. Please check your API key.")


class LLMRateLimitError(LLMError):
    """Raised when provider rate limit or quota is exceeded."""
    def __init__(self, message: str = "Provider rate limit or quota exceeded."):
        super().__init__(message, safe_message="LLM provider rate limit exceeded. Please try again shortly.")


class LLMTimeoutError(LLMError):
    """Raised when the LLM provider request times out."""
    def __init__(self, message: str = "LLM request timed out."):
        super().__init__(message, safe_message="The AI provider request timed out. Please try again.")


class ToolExecutionError(JarvisError):
    """Raised when an approved tool fails during execution."""
    pass


class DocumentProcessingError(JarvisError):
    """Raised when document extraction or parsing fails."""
    pass


class DocumentNotFoundError(JarvisError):
    """Raised when a requested document ID does not exist."""
    pass


class SessionNotFoundError(JarvisError):
    """Raised when a requested conversation session does not exist."""
    pass
