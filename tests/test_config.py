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
