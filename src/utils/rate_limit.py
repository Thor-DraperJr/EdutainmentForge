"""In-process rate limiting utilities for Flask endpoints.

Hackathon scope: simple fixed-window counters. Not safe for multi-instance horizontal scaling.
"""
from __future__ import annotations

import os
import time
from functools import wraps
from typing import Callable, Dict, Tuple
from flask import request, jsonify

from utils.logger import get_logger

logger = get_logger(__name__)

# Structure: key -> (window_start_epoch, count)
_counters: Dict[str, Tuple[int, int]] = {}


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


RATE_LIMIT_WINDOW_SECONDS = _get_env_int("RATE_LIMIT_WINDOW_SECONDS", 60)
RATE_LIMIT_MAX_REQUESTS = _get_env_int("RATE_LIMIT_MAX_REQUESTS", 10)
GLOBAL_PROCESSING_MAX = _get_env_int("RATE_LIMIT_GLOBAL_PROCESSING_MAX", 30)


def _increment(key: str, max_requests: int, window_seconds: int) -> bool:
    now = int(time.time())
    window_start = now - (now % window_seconds)
    current = _counters.get(key)
    if not current or current[0] != window_start:
        _counters[key] = (window_start, 1)
        return True
    # same window
    if current[1] >= max_requests:
        return False
    _counters[key] = (current[0], current[1] + 1)
    return True


def rate_limit(endpoint_max: int = None, window_seconds: int = None, global_category: str = None):
    """Decorator to rate limit an endpoint.

    Args:
        endpoint_max: Override per-client (IP) max within window
        window_seconds: Window size override
        global_category: If set, apply an additional global category cap
    """
    endpoint_max = endpoint_max or RATE_LIMIT_MAX_REQUESTS
    window_seconds = window_seconds or RATE_LIMIT_WINDOW_SECONDS

    def decorator(f: Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
            key = f"rl:{f.__name__}:{client_ip}"  # per endpoint+IP
            allowed = _increment(key, endpoint_max, window_seconds)
            if not allowed:
                retry_after = window_seconds - (int(time.time()) % window_seconds)
                logger.debug(f"Rate limit hit for {client_ip} on {f.__name__}")
                return jsonify({
                    "error": "rate_limited",
                    "retry_after": retry_after,
                    "detail": "Too many requests; slow down."
                }), 429

            if global_category:
                gkey = f"global:{global_category}"
                if not _increment(gkey, GLOBAL_PROCESSING_MAX, window_seconds):
                    retry_after = window_seconds - (int(time.time()) % window_seconds)
                    return jsonify({
                        "error": "rate_limited_global",
                        "retry_after": retry_after,
                        "detail": "System is busy; try again shortly."
                    }), 429

            return f(*args, **kwargs)
        return wrapped
    return decorator
