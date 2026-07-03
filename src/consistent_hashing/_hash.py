"""Shared deterministic 64-bit hash used across all implementations."""

from __future__ import annotations

import hashlib

_RING = 1 << 64  # hash space [0, 2^64)


def sha64(obj: object, seed: int) -> int:
    """Deterministic 64-bit hash of any object, parameterised by seed."""
    raw = f"{seed}:{obj!r}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")
