"""Shared HTTP helpers for the SVG chart endpoints."""

import hashlib
from datetime import datetime
from io import BytesIO
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

# Charts are per-user (behind auth), so cache them privately for an hour.
CACHE_CONTROL = "private, max-age=3600"


def validate_time_range(start: Optional[datetime], end: Optional[datetime]) -> None:
    """Reject an inverted time range with a 422."""
    if start is not None and end is not None and start > end:
        raise HTTPException(status_code=422, detail="start must not be after end")


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

    return StreamingResponse(render(), media_type="image/svg+xml", headers=headers)
