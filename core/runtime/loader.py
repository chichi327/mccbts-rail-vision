from __future__ import annotations

import importlib
from typing import Any

from core.base.detector import BaseDetector
from core.base.estimator import BaseEstimator


def load_class(module_name: str, class_name: str) -> type:
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def load_pipeline_steps(step_names: list[str], algorithms: dict[str, Any]) -> list[BaseDetector | BaseEstimator]:
    loaded: list[BaseDetector | BaseEstimator] = []
    for name in step_names:
        spec = algorithms.get(name)
        if spec is None:
            raise KeyError(f"algorithm {name} not in algorithms.yaml")
        if not spec.get("enabled", True):
            continue
        cls = load_class(spec["module"], spec["class"])
        inst = cls()
        inst.load(spec.get("config") or {})
        loaded.append(inst)
    return loaded
