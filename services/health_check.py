from __future__ import annotations

from typing import Any, Mapping


def health_snapshot(latest_payloads: Mapping[str, Any] | None = None, extra: dict | None = None) -> dict:
    heartbeats = []
    if latest_payloads is not None:
        heartbeats = [latest_payloads[key] for key in list(latest_payloads.keys())]
    issues = []
    for hb in heartbeats:
        issues.extend(hb.get("issues") or [])
    payload = {
        "status": "ok" if not issues else "degraded",
        "service": "mccbts-rail-vision",
        "heartbeats": heartbeats,
    }
    if extra:
        payload.update(extra)
    return payload
