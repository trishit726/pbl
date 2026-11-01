"""Single-line structured JSON request logging and audit persistence."""

import json
import logging as std_logging
from datetime import datetime, timezone
from typing import Any

logger = std_logging.getLogger("lms.audit")


def request_log_record(*, request_id: str, user_id: str | None, role: str | None,
                       device_id: str | None, source_ip: str | None, endpoint: str,
                       method: str, status: int, response_size_bytes: int,
                       latency_ms: float) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "user_id": user_id,
        "role": role,
        "device_id": device_id,
        "source_ip": source_ip,
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "response_size_bytes": response_size_bytes,
        "latency_ms": round(latency_ms, 3),
    }


def emit_request_log(record: dict[str, Any]) -> None:
    """Emit exactly one JSON log line; caller may separately persist audit row."""
    logger.info(json.dumps(record, separators=(",", ":"), default=str))

