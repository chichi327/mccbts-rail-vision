from core.runtime.config import load_app_config
from core.runtime.loader import load_pipeline_steps
from core.base.detector import BaseDetector
from core.base.estimator import BaseEstimator


def test_load_person_pipeline():
    cfg = load_app_config("config")
    pipe = next(p for p in cfg.pipelines if p["id"] == "person_vehicle")
    steps = load_pipeline_steps(pipe["steps"], cfg.algorithms)
    assert isinstance(steps[0], BaseDetector)
    assert isinstance(steps[1], BaseEstimator)
    for s in steps:
        s.release()
