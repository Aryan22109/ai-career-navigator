"""Small in-memory sliding-window rate limiter (per client IP).

Good enough for a single-process deployment. For several workers or servers,
swap the store for Redis.
"""
import time
from collections import defaultdict, deque
from functools import wraps
from threading import Lock

from flask import current_app, jsonify, request

_hits: dict[str, deque] = defaultdict(deque)
_lock = Lock()
WINDOW_SECONDS = 60


def reset():
    with _lock:
        _hits.clear()


def rate_limited(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        limit = current_app.config.get("RATE_LIMIT_PER_MIN", 20)
        if limit <= 0:
            return view(*args, **kwargs)
        now = time.monotonic()
        key = request.remote_addr or "unknown"
        with _lock:
            q = _hits[key]
            while q and now - q[0] > WINDOW_SECONDS:
                q.popleft()
            if len(q) >= limit:
                retry = int(WINDOW_SECONDS - (now - q[0])) + 1
                resp = jsonify(error="Too many requests. Please wait a moment and try again.")
                resp.status_code = 429
                resp.headers["Retry-After"] = str(retry)
                return resp
            q.append(now)
        return view(*args, **kwargs)

    return wrapper
