from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    cameras: list[dict[str, Any]]
    algorithms: dict[str, Any]
    pipelines: list[dict[str, Any]]
    system: dict[str, Any]
    config_dir: Path
    backend: dict[str, Any] = field(default_factory=dict)


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_app_config(config_dir: str | Path) -> AppConfig:
    root = Path(config_dir)
    cameras = _load_yaml(root / "cameras.yaml").get("cameras") or []
    algorithms = _load_yaml(root / "algorithms.yaml").get("algorithms") or {}
    pipelines = _load_yaml(root / "pipelines.yaml").get("pipelines") or []
    system = _load_yaml(root / "system.yaml").get("system") or {}
    backend = dict(system.get("backend") or {})
    backend["events_url"] = os.environ.get("BACKEND_EVENTS_URL", backend.get("events_url", ""))
    backend["heartbeat_url"] = os.environ.get("BACKEND_HEARTBEAT_URL", backend.get("heartbeat_url", ""))
    backend["token"] = os.environ.get("BACKEND_TOKEN", backend.get("token", ""))
    system["backend"] = backend
    return AppConfig(
        cameras=cameras,
        algorithms=algorithms,
        pipelines=pipelines,
        system=system,
        config_dir=root,
        backend=backend,
    )
