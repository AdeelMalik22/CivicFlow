import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

request_logger = logging.getLogger("civicflow.request")


class RequestContextMiddleware:
    """Attach a correlation ID and emit one structured record per response."""

    request_id_header = "X-Request-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = self._request_id(request)
        request.request_id = request_id
        started_at = time.monotonic()

        response = self.get_response(request)
        response[self.request_id_header] = request_id

        request_logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
                "user_id": (
                    str(request.user.pk)
                    if hasattr(request, "user") and request.user.is_authenticated
                    else None
                ),
            },
        )
        return response

    def _request_id(self, request: HttpRequest) -> str:
        supplied_id = request.headers.get(self.request_id_header, "").strip()
        try:
            return str(uuid.UUID(supplied_id))
        except (ValueError, AttributeError):
            return str(uuid.uuid4())
