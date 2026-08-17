"""
Structured JSON logging + Prometheus metrics (optional dependency).
"""
import json
import logging
import os
import sys
from typing import Optional

try:
    from prometheus_client import Counter, Histogram

    AGENT_RUNS = Counter("stratum_agent_runs_total", "Agent executions", ["vertical", "agent"])
    AGENT_DURATION = Histogram("stratum_agent_duration_seconds", "Agent execution time", ["vertical", "agent"])
except ImportError:  # pragma: no cover
    AGENT_RUNS = AGENT_DURATION = None


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging(level: Optional[str] = None) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel((level or os.getenv("LOG_LEVEL", "INFO")).upper())


def track_metric(name: str, labels: Optional[dict] = None, value: float = 1.0) -> None:
    if name == "agent_runs" and AGENT_RUNS is not None:
        AGENT_RUNS.labels(**(labels or {})).inc(value)
