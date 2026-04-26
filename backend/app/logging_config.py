import json
import logging
import logging.config
import os
import traceback
from datetime import datetime, timezone
from typing import Any

try:
    from opentelemetry import trace
except ImportError:  # pragma: no cover - OpenTelemetry is optional outside instrumented containers.
    trace = None


_STANDARD_LOG_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}


class EcsJsonFormatter(logging.Formatter):
    """Format stdlib LogRecords as ECS-compatible JSON for container stdout."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        log: dict[str, Any] = {
            "@timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat().replace("+00:00", "Z"),
            "ecs.version": "8.11.0",
            "log.level": record.levelname.lower(),
            "log.logger": record.name,
            "message": message,
            "service.name": os.getenv("SERVICE_NAME", "wkpoule-api"),
            "event.dataset": os.getenv("SERVICE_NAME", "wkpoule-api"),
            "process.pid": record.process,
            "process.thread.name": record.threadName,
            "log.origin.file.name": record.pathname,
            "log.origin.file.line": record.lineno,
            "log.origin.function": record.funcName,
        }

        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            log["error.type"] = exc_type.__name__ if exc_type else None
            log["error.message"] = str(exc_value) if exc_value else message
            log["error.stack_trace"] = "".join(traceback.format_exception(*record.exc_info))

        if trace:
            span_context = trace.get_current_span().get_span_context()
            if span_context.is_valid:
                log["trace.id"] = f"{span_context.trace_id:032x}"
                log["span.id"] = f"{span_context.span_id:016x}"

        for key, value in record.__dict__.items():
            if key not in _STANDARD_LOG_RECORD_KEYS and not key.startswith("_"):
                log[key] = value

        return json.dumps(log, default=str, ensure_ascii=False)


def _otel_logs_enabled() -> bool:
    exp = os.getenv("OTEL_LOGS_EXPORTER", "").strip().lower()
    return bool(exp) and exp not in ("none", "false", "off")


def _attach_otlp_log_export_after_dictconfig() -> None:
    """dictConfig replaces root handlers and drops the OTLP handler from bootstrap; re-attach here."""
    if not _otel_logs_enabled():
        return
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
    except ImportError:
        return
    inst = LoggingInstrumentor()
    if inst.is_instrumented_by_opentelemetry:
        inst.uninstrument()
    inst.instrument()


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "ecs": {
                    "()": "app.logging_config.EcsJsonFormatter",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "ecs",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "handlers": ["default"],
                "level": level,
            },
            "loggers": {
                # Propagate to root so ECS stdout + OTLP handler on root see access/error lines too.
                "uvicorn": {"handlers": [], "level": level, "propagate": True},
                "uvicorn.error": {"handlers": [], "level": level, "propagate": True},
                "uvicorn.access": {"handlers": [], "level": level, "propagate": True},
            },
        }
    )
    _attach_otlp_log_export_after_dictconfig()
