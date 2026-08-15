from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Literal

import numpy as np
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class AppConfig(BaseModel):
    name: str = "hybrid-rf-scanner"
    node_id: str = "scanner-01"
    log_level: str = "INFO"
    log_file: str = "logs/scanner.log"
    log_rotation: str = "25 MB"
    loop_hz: float = Field(default=20.0, gt=0, le=200)
    recording_enabled: bool = True
    recording_path: str = "recordings/events.jsonl"
    recording_queue_size: int = Field(default=10000, ge=100, le=1_000_000)
    privacy_mode: bool = True


class RadarConfig(BaseModel):
    enabled: bool = True
    config_port: str
    data_port: str
    config_baud: int = Field(default=115200, ge=1200)
    data_baud: int = Field(default=921600, ge=9600)
    read_timeout_s: float = Field(default=0.20, gt=0, le=5)
    cli_response_timeout_s: float = Field(default=0.35, gt=0, le=5)
    profile_path: str
    header_format: Literal["xwr68xx_40"] = "xwr68xx_40"
    tlv_length_mode: Literal["auto", "includes_header", "payload_only"] = "auto"
    max_packet_bytes: int = Field(default=262144, ge=1024, le=4_000_000)
    max_coordinate_m: float = Field(default=50.0, gt=0, le=500)
    reconnect_initial_s: float = Field(default=0.5, gt=0, le=30)
    reconnect_max_s: float = Field(default=10.0, gt=0, le=300)


class VisionConfig(BaseModel):
    enabled: bool = True
    serial_number: str | None = None
    width: int = Field(default=640, ge=160, le=1920)
    height: int = Field(default=480, ge=120, le=1080)
    fps: int = Field(default=30, ge=6, le=90)
    timeout_ms: int = Field(default=1000, ge=50, le=10000)
    max_points: int = Field(default=30000, ge=1000, le=250000)
    min_depth_m: float = Field(default=0.20, ge=0.05, le=5)
    max_depth_m: float = Field(default=6.0, gt=0.1, le=30)
    reconnect_initial_s: float = Field(default=0.5, gt=0, le=30)
    reconnect_max_s: float = Field(default=10.0, gt=0, le=300)

    @model_validator(mode="after")
    def depth_order(self):
        if self.max_depth_m <= self.min_depth_m:
            raise ValueError("max_depth_m must exceed min_depth_m")
        return self


class SyncConfig(BaseModel):
    max_skew_ms: float = Field(default=60.0, gt=0, le=1000)
    buffer_size: int = Field(default=120, ge=4, le=5000)
    stale_sensor_ms: float = Field(default=1500.0, gt=50, le=60000)


class FusionConfig(BaseModel):
    radar_to_camera: list[list[float]]
    calibration_validated: bool = False
    calibration_rmse_m: float | None = Field(default=None, ge=0, le=10)
    calibration_p95_m: float | None = Field(default=None, ge=0, le=10)
    max_pairing_distance_m: float = Field(default=0.35, gt=0, le=5)
    min_snr_db: float = Field(default=6.0, ge=-50, le=100)
    min_confidence: float = Field(default=0.35, ge=0, le=1)
    radar_sigma_at_high_snr_m: float = Field(default=0.035, gt=0, le=2)
    radar_sigma_at_low_snr_m: float = Field(default=0.18, gt=0, le=5)
    vision_sigma_m: float = Field(default=0.025, gt=0, le=2)
    no_vision_penalty: float = Field(default=0.82, gt=0, le=1)

    @field_validator("radar_to_camera")
    @classmethod
    def validate_transform(cls, value: list[list[float]]) -> list[list[float]]:
        arr = np.asarray(value, dtype=np.float64)
        if arr.shape != (4, 4):
            raise ValueError("radar_to_camera must be a 4x4 matrix")
        if not np.isfinite(arr).all():
            raise ValueError("radar_to_camera must contain only finite values")
        if not np.allclose(arr[3], [0, 0, 0, 1], atol=1e-6):
            raise ValueError("transform last row must be [0,0,0,1]")
        r = arr[:3, :3]
        if not np.allclose(r.T @ r, np.eye(3), atol=0.08):
            raise ValueError("transform rotation is not approximately orthonormal")
        if not math.isclose(float(np.linalg.det(r)), 1.0, abs_tol=0.08):
            raise ValueError("transform rotation determinant must be approximately +1")
        return value




class CalibrationMonitorConfig(BaseModel):
    enabled: bool = True
    window_size: int = Field(default=300, ge=20, le=10000)
    min_samples: int = Field(default=30, ge=5, le=5000)
    median_warn_m: float = Field(default=0.12, gt=0, le=5)
    p95_warn_m: float = Field(default=0.25, gt=0, le=10)
    fail_readiness_on_drift: bool = False


class TrackerConfig(BaseModel):
    enabled: bool = True
    association_gate_m: float = Field(default=0.70, gt=0, le=10)
    confirmation_hits: int = Field(default=3, ge=1, le=100)
    max_misses: int = Field(default=8, ge=1, le=500)
    process_noise: float = Field(default=0.8, gt=0, le=100)
    default_measurement_sigma_m: float = Field(default=0.12, gt=0, le=5)


class MapConfig(BaseModel):
    enabled: bool = True
    voxel_size_m: float = Field(default=0.10, gt=0.01, le=5)
    hit_log_odds: float = Field(default=0.85, gt=0, le=10)
    decay_per_s: float = Field(default=0.04, ge=0, le=10)
    prune_below: float = Field(default=0.08, ge=0, le=10)
    max_voxels: int = Field(default=30000, ge=100, le=2_000_000)


class ApiConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(default=8080, ge=1, le=65535)
    auth_token_env: str = "HYBRID_SCANNER_API_TOKEN"
    allow_unauthenticated_loopback: bool = True

    def token(self) -> str | None:
        return os.getenv(self.auth_token_env)


class ResearchConfig(BaseModel):
    active_scan_guidance: bool = True
    raw_adc_pipeline_enabled: bool = False
    multi_node_fusion_enabled: bool = False
    learned_classifier_enabled: bool = False


class ScannerConfig(BaseModel):
    app: AppConfig
    radar: RadarConfig
    vision: VisionConfig
    sync: SyncConfig = SyncConfig()
    fusion: FusionConfig
    calibration_monitor: CalibrationMonitorConfig = CalibrationMonitorConfig()
    tracker: TrackerConfig = TrackerConfig()
    mapping: MapConfig = MapConfig()
    api: ApiConfig
    research: ResearchConfig = ResearchConfig()


def load_config(path: str | Path) -> ScannerConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a YAML mapping")
    return ScannerConfig.model_validate(raw)
