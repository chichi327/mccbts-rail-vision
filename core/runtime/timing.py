from __future__ import annotations

import os
from typing import Any


def _env_enabled() -> bool | None:
    raw = os.environ.get("TIMING_ENABLED")
    if raw is None or raw.strip() == "":
        return None
    return raw.strip().lower() in ("1", "true", "yes", "on")


def apply_timing_overrides(system: dict[str, Any]) -> None:
    timing = dict(system.get("timing") or {})
    env = _env_enabled()
    if env is not None:
        timing["enabled"] = env
    system["timing"] = timing


def timing_enabled(system: dict[str, Any]) -> bool:
    return bool((system.get("timing") or {}).get("enabled", False))


def timing_log_every_n(system: dict[str, Any]) -> int:
    n = int((system.get("timing") or {}).get("log_every_n", 30))
    return max(1, n)
