"""
DSRA V2 — Structured Logging
==============================
Configures structlog for JSON-compatible, async-safe, context-bound logging.

Usage:
    from app.core.logging import get_logger
    log = get_logger(__name__)

    log.info("agent_started", agent="PlannerAgent", session_id=str(session_id))
    log.error("fetch_failed", source="arxiv", error=str(e), duration_ms=elapsed)
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config.settings import get_settings


def _add_app_context(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application-level context to every log entry."""
    settings = get_settings()
    event_dict["app_version"] = settings.app_version
    event_dict["env"] = settings.app_env
    return event_dict


def _drop_color_message_key(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Uvicorn uses 'color_message' key — drop it to avoid duplicate noise
    in structured output.
    """
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """
    Configure structlog and standard library logging.
    Must be called once at application startup (in app/main.py).
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _add_app_context,
        _drop_color_message_key,
    ]

    if settings.log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Quiet noisy libraries
    for noisy in ["uvicorn.access", "sqlalchemy.engine", "httpx"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger bound to the given module name."""
    return structlog.get_logger(name)
