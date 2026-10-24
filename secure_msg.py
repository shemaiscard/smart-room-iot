"""Sealed MQTT payloads shared by the dashboard, the simulator and the firmware.

The broker is public, so anyone can subscribe to and publish on our topics. Every
message is therefore encrypted and authenticated with AES-256-GCM under a key that
only the board, the dashboard and the simulator know:

    <timestamp in ms since 1970>|<hex of nonce (12 bytes) + ciphertext + tag (16 bytes)>

The topic and the timestamp are authenticated as associated data ("<topic>|<timestamp>"),
so a reading cannot be replayed as a command and the timestamp cannot be changed. A
receiver rejects a bad tag, a timestamp more than MAX_SKEW_MS away from its own clock,
and (for commands) any timestamp not newer than the last one it accepted. The firmware
implements the same format in C (SecureMsg.h).
"""
from __future__ import annotations

import hashlib
import os
import time

from Crypto.Cipher import AES

MAX_SKEW_MS = 30_000
KEY_CONTEXT = b"smart-room-v2|"


def now_ms() -> int:
    return int(time.time() * 1000)


def derive_key(secret: bytes) -> bytes:
    """The 256-bit AES key from the shared secret (the same on the board)."""
    return hashlib.sha256(KEY_CONTEXT + secret).digest()


def seal(secret: bytes, topic: str, body: str, ts_ms: int | None = None, nonce: bytes | None = None) -> str:
    ts_ms = now_ms() if ts_ms is None else ts_ms
    nonce = os.urandom(12) if nonce is None else nonce
    cipher = AES.new(derive_key(secret), AES.MODE_GCM, nonce=nonce)
    cipher.update(f"{topic}|{ts_ms}".encode())
    ciphertext, tag = cipher.encrypt_and_digest(body.encode())
    return f"{ts_ms}|{(nonce + ciphertext + tag).hex()}"


def unseal(secret: bytes, topic: str, payload: str, newer_than: int | None = None,
           now: int | None = None, max_skew_ms: int | None = MAX_SKEW_MS) -> tuple[str, int] | None:
    """Return (body, timestamp) for an authentic message, or None.

    max_skew_ms=None skips the freshness check (used for the retained status).
    """
    try:
        ts_str, blob_hex = payload.split("|", 1)
        ts_ms = int(ts_str)
        blob = bytes.fromhex(blob_hex)
        if len(blob) < 28:
            return None
        cipher = AES.new(derive_key(secret), AES.MODE_GCM, nonce=blob[:12])
        cipher.update(f"{topic}|{ts_ms}".encode())
        body = cipher.decrypt_and_verify(blob[12:-16], blob[-16:]).decode()
    except (ValueError, UnicodeDecodeError):
        return None
    now = now_ms() if now is None else now
    if max_skew_ms is not None and abs(now - ts_ms) > max_skew_ms:
        return None
    if newer_than is not None and ts_ms <= newer_than:
        return None
    return body, ts_ms
