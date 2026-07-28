"""
DevVerse AI - Logging Configuration

Structured logging with correlation IDs for distributed tracing.
Integrates with OpenTelemetry for observability.
"""

import logging
import sys
import uuid
from typing import Any, Dict
from contextvars import ContextVar
from fastapi import Request

import structlog
from core.config import settings


# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    correlation_id_var.set(correlation_id)


async def correlation_id_middleware(request: Request, call_next):
    """
    Middleware to add correlation ID to each request.
    
    Generates a unique ID for tracking requests across services.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


class CorrelationIdFilter(logging.Filter):
    """Logging filter that adds correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    In development: Pretty-printed console output
    In production: JSON format for log aggregation
    """
    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add correlation ID to all logs
            structlog.contextvars.merge_contextvars,
            
            # Add standard logging fields
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            
            # Handle exceptions
            structlog.tracebacks.add_exception_showlocals,
            
            # Format for output
            structlog.dev.ConsoleRenderer(colors=True) 
                if settings.is_development 
                else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(CorrelationIdFilter())
    
    # Only add formatter in development
    if settings.is_development:
        formatter = logging.Formatter(
            "%(asctime)s [%(correlation_id)s] %(levelname)s %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
