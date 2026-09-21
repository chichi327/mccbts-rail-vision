from core.runtime.config import load_app_config
from core.runtime.timing import apply_timing_overrides, timing_enabled, timing_log_every_n


def test_timing_defaults_off(monkeypatch):
    monkeypatch.delenv("TIMING_ENABLED", raising=False)
    system: dict = {}
    apply_timing_overrides(system)
    assert timing_enabled(system) is False
    assert timing_log_every_n(system) == 30


def test_timing_yaml_and_log_every_n(monkeypatch):
    monkeypatch.delenv("TIMING_ENABLED", raising=False)
    system = {"timing": {"enabled": True, "log_every_n": 1}}
    apply_timing_overrides(system)
    assert timing_enabled(system) is True
    assert timing_log_every_n(system) == 1


def test_timing_env_overrides_yaml(monkeypatch):
    monkeypatch.setenv("TIMING_ENABLED", "true")
    system = {"timing": {"enabled": False}}
    apply_timing_overrides(system)
    assert timing_enabled(system) is True
    monkeypatch.setenv("TIMING_ENABLED", "0")
    system = {"timing": {"enabled": True}}
    apply_timing_overrides(system)
    assert timing_enabled(system) is False


def test_load_app_config_has_timing_block(monkeypatch):
    monkeypatch.delenv("TIMING_ENABLED", raising=False)
    cfg = load_app_config("config")
    assert "timing" in cfg.system
    assert timing_enabled(cfg.system) is False
