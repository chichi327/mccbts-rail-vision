from __future__ import annotations


def health_snapshot(extra: dict | None = None) -> dict:
    payload = {"status": "ok", "service": "mccbts-rail-vision"}
    if extra:
        payload.update(extra)
    return payload
