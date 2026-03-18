from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = Lock()


def resolve_client_identifier(request: Request, *, extra: str = "") -> str:
    ip = request.client.host if request.client and request.client.host else "unknown"
    normalized_extra = extra.strip().lower()
    return f"{ip}|{normalized_extra}" if normalized_extra else ip


def enforce_rate_limit(bucket: str, identifier: str, *, limit: int, window_seconds: int) -> None:
    now = monotonic()
    key = f"{bucket}:{identifier}"
    window = max(1, int(window_seconds))
    max_calls = max(1, int(limit))

    with _LOCK:
        hits = _BUCKETS[key]
        cutoff = now - window
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= max_calls:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

        hits.append(now)
