"""
Logging configuration for the application.
Structured JSON in production, human-readable in development.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from app.config import settings


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        from app.core.middleware import request_id_var  # deferred to avoid circular import

        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get("-"),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Configure application logging."""

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    if settings.DEBUG:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        formatter = JsonFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.addHandler(handler)

    # Suppress noisy libraries
    for lib in ("urllib3", "httpx", "httpcore", "watchfiles", "multipart"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

