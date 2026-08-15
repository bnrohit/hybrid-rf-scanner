from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np


def _finite_vec3(values: tuple[float, float, float]) -> bool:
    return all(np.isfinite(v) for v in values)


@dataclass(slots=True)
class RadarPoint:
    x: float
    y: float
    z: float
    velocity: float
    snr_db: float | None = None
    noise_db: float | None = None

    @property
    def position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=np.float64)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RadarFrame:
    frame_number: int
    timestamp_ns: int
    points: list[RadarPoint]
    parser_warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class VisionFrame:
    timestamp_ns: int
    points_xyz: np.ndarray
    gyro_xyz: np.ndarray | None = None
    accel_xyz: np.ndarray | None = None
    device_timestamp_ms: float | None = None


@dataclass(slots=True)
class FusedMeasurement:
    position_xyz: tuple[float, float, float]
    covariance_diag_m2: tuple[float, float, float]
    radial_velocity_mps: float
    snr_db: float | None
    nearest_depth_distance_m: float | None
    confidence: float
    radar_trust: float
    vision_trust: float
    visibility_state: str = "unknown"
    label: str = "radar-correlated-target"

    def __post_init__(self) -> None:
        if not _finite_vec3(self.position_xyz):
            raise ValueError("position must be finite")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TrackSnapshot:
    track_id: int
    position_xyz: tuple[float, float, float]
    velocity_xyz_mps: tuple[float, float, float]
    covariance_diag: tuple[float, float, float, float, float, float]
    confidence: float
    hits: int
    misses: int
    confirmed: bool
    age_s: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScanGuidance:
    action: str
    direction_xyz: tuple[float, float, float]
    reason: str
    target_track_id: int | None = None
    expected_information_gain: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
