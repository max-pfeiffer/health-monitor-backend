"""Shared HTTP helpers for the SVG chart endpoints."""

import hashlib
from datetime import datetime
from io import BytesIO
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import StreamingResponse

# Charts are per-user (behind auth), so cache them privately for an hour.
CACHE_CONTROL = "private, max-age=3600"


class SVGChartResponse(StreamingResponse):
    """A ``StreamingResponse`` documented as an SVG image in OpenAPI."""

    media_type = "image/svg+xml"


# Shared OpenAPI ``responses`` for the SVG chart endpoints. FastAPI already
# documents 422 automatically for the query parameters; this fills in the SVG
# success body and the conditional 304 that ``chart_response`` can return.
CHART_RESPONSES: dict = {
    200: {
        "description": "Rendered SVG chart for the requested time range.",
        "content": {
            "image/svg+xml": {"schema": {"type": "string", "format": "binary"}}
        },
    },
    304: {
        "description": (
            "The chart is unchanged since the ETag supplied in the "
            "`If-None-Match` request header. No body is returned."
        ),
    },
}


def validate_time_range(start: Optional[datetime], end: Optional[datetime]) -> None:
    """Reject an inverted time range with a 422.

    Raised as a ``RequestValidationError`` so the response body matches the
    structured ``{"detail": [{"type", "loc", "msg", "input"}]}`` payload that
    FastAPI emits for its own query-parameter validation errors.
    """
    if start is not None and end is not None and start > end:
        raise RequestValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("query", "end"),
                    "msg": "Value error, end must not be before start",
                    "input": end.isoformat(),
                }
            ]
        )


def _compute_etag(parts: list, records: list) -> str:
    latest = max((r.measured_at for r in records), default=None)
    raw = "|".join(str(p) for p in [*parts, len(records), latest])
    return '"' + hashlib.md5(raw.encode()).hexdigest() + '"'


def chart_response(
    request: Request,
    records: list,
    render: Callable[[], BytesIO],
    *,
    etag_parts: list,
) -> Response:
    """Return a cached SVG chart response with ETag / 304 handling.

    The ETag is derived from the request parameters plus the record count and
    latest ``measured_at``, so it changes whenever the rendered chart would. On
    an ``If-None-Match`` hit we return 304 without re-rendering.
    """
    etag = _compute_etag(etag_parts, records)
    headers = {"ETag": etag, "Cache-Control": CACHE_CONTROL}

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)

    return SVGChartResponse(render(), headers=headers)
