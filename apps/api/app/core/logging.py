from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime

SECRET = re.compile(r"(?i)(authorization|api[_-]?key|password|token|secret)(\s*[=:]\s*)([^\s,;]+)")


def redact(value: str) -> str:
    return SECRET.sub(r"\1\2[REDACTED]", value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        for key in ("request_id", "incident_id", "event_type"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
