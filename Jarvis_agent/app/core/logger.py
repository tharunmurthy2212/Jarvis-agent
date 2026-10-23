import logging
import re
import sys

# Pattern to mask sensitive keys, tokens, and authorization headers
SECRET_PATTERN = re.compile(
    r'(?i)(api[-_]?key|authorization|bearer|secret|password|token)\s*[:=]\s*["\']?([^"\'\s,;]+)["\']?'
)

class SafeFormatter(logging.Formatter):
    """Logging formatter that scrubs API keys and sensitive tokens."""
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return SECRET_PATTERN.sub(r'\1: [REDACTED]', original)


def setup_logger(name: str = "jarvis") -> logging.Logger:
    """Set up and return the application logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            SafeFormatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger()
