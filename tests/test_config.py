from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from hybrid_scanner.config import ScannerConfig, load_config


def test_default_config_loads():
    cfg = load_config(Path("config/scanner_config.yaml"))
    assert cfg.app.loop_hz == 20
    assert cfg.fusion.radar_to_camera[3] == [0.0, 0.0, 0.0, 1.0]
    assert cfg.fusion.calibration_validated is False


def test_bad_transform_rejected():
    raw = yaml.safe_load(Path("config/scanner_config.yaml").read_text())
    raw = deepcopy(raw)
    raw["fusion"]["radar_to_camera"][3] = [0, 0, 0, 0]
    with pytest.raises(Exception):
        ScannerConfig.model_validate(raw)


def test_validated_calibration_requires_quality_metrics():
    raw = yaml.safe_load(Path("config/scanner_config.yaml").read_text())
    raw = deepcopy(raw)
    raw["fusion"]["calibration_validated"] = True
    with pytest.raises(Exception):
        ScannerConfig.model_validate(raw)


def test_calibration_monitor_sample_window_rejected():
    raw = yaml.safe_load(Path("config/scanner_config.yaml").read_text())
    raw = deepcopy(raw)
    raw["calibration_monitor"]["window_size"] = 20
    raw["calibration_monitor"]["min_samples"] = 30
    with pytest.raises(Exception):
        ScannerConfig.model_validate(raw)


def test_api_environment_override(monkeypatch):
    monkeypatch.setenv("HYBRID_SCANNER_API_HOST", "0.0.0.0")
    monkeypatch.setenv("HYBRID_SCANNER_API_PORT", "9090")
    cfg = load_config(Path("config/scanner_config.yaml"))
    assert cfg.api.host == "0.0.0.0"
    assert cfg.api.port == 9090
