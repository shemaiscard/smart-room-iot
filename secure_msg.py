"""Signed MQTT payloads shared by the dashboard, the simulator and the firmware.

The broker is public, so anyone can publish on our topics. Every message
therefore carries a timestamp and an HMAC-SHA256 tag made with a key that only
the board, the dashboard and the simulator know:

    <body>|<timestamp in ms since 1970>|<hex HMAC-SHA256(key, "<topic>|<body>|<timestamp>")>

The topic is part of the signed text, so a reading cannot be replayed as a
command. A receiver rejects a bad tag, a timestamp more than MAX_SKEW_MS away
from its own clock, and (for commands) any timestamp not newer than the last
one it accepted. The firmware implements the same format in C.
"""
from __future__ import annotations

import hashlib
import hmac
import time

MAX_SKEW_MS = 30_000


def now_ms() -> int:
    return int(time.time() * 1000)


def tag(key: bytes, topic: str, body: str, ts_ms: int) -> str:
    return hmac.new(key, f"{topic}|{body}|{ts_ms}".encode(), hashlib.sha256).hexdigest()


def sign(key: bytes, topic: str, body: str, ts_ms: int | None = None) -> str:
    ts_ms = now_ms() if ts_ms is None else ts_ms
    return f"{body}|{ts_ms}|{tag(key, topic, body, ts_ms)}"


def verify(key: bytes, topic: str, payload: str, newer_than: int | None = None,
           now: int | None = None, max_skew_ms: int | None = MAX_SKEW_MS) -> tuple[str, int] | None:
    """Return (body, timestamp) for a valid message, or None.

    max_skew_ms=None skips the freshness check (used for the retained status).
    """
    try:
        body, ts_str, mac = payload.rsplit("|", 2)
        ts_ms = int(ts_str)
    except ValueError:
        return None
    if not hmac.compare_digest(mac, tag(key, topic, body, ts_ms)):
        return None
    now = now_ms() if now is None else now
    if max_skew_ms is not None and abs(now - ts_ms) > max_skew_ms:
        return None
    if newer_than is not None and ts_ms <= newer_than:
        return None
    return body, ts_ms
