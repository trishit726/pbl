"""Request correlation and audit middleware for FastAPI services."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logging import emit_request_log, request_log_record


class RequestAuditMiddleware(BaseHTTPMiddleware):
    """Capture gateway identity headers and emit a structured request record.

    X-Forwarded-For is only trusted because services are intended to be reachable
    inside a private network behind the gateway/load balancer.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.device_id = request.headers.get("X-Device-Id")
        forwarded = request.headers.get("X-Forwarded-For", "")
        source_ip = forwarded.split(",", 1)[0].strip() or None
        started = time.perf_counter()
        response: Response
        try:
            response = await call_next(request)
        except Exception:
            response = Response(status_code=500)
            raise
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            response_bytes = int(response.headers.get("content-length", "0")) if "response" in locals() else 0
            principal = getattr(request.state, "principal", {})
            emit_request_log(request_log_record(
                request_id=request_id,
                user_id=principal.get("user_id"),
                role=principal.get("role"),
                device_id=request.state.device_id,
                source_ip=source_ip,
                endpoint=request.url.path,
                method=request.method,
                status=response.status_code if "response" in locals() else 500,
                response_size_bytes=response_bytes,
                latency_ms=elapsed,
            ))
        response.headers["X-Request-Id"] = request_id
        return response

