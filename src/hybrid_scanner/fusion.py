from __future__ import annotations

import math

import numpy as np
from scipy.spatial import cKDTree

from hybrid_scanner.models import FusedMeasurement, RadarFrame, RadarPoint, VisionFrame


class FusionEngine:
    """Uncertainty-aware radar/depth correlation.

    This is deliberately not an object-identity classifier. It converts sensor
    agreement, SNR, calibration, and sensor trust into a bounded measurement
    confidence and covariance that downstream tracking can reason about.
    """

    def __init__(
        self,
        *,
        radar_to_camera: list[list[float]],
        max_pairing_distance_m: float,
        min_snr_db: float,
        min_confidence: float,
        radar_sigma_at_high_snr_m: float,
        radar_sigma_at_low_snr_m: float,
        vision_sigma_m: float,
        no_vision_penalty: float,
    ) -> None:
        self.transform = np.asarray(radar_to_camera, dtype=np.float64)
        self.max_pairing_distance_m = max_pairing_distance_m
        self.min_snr_db = min_snr_db
        self.min_confidence = min_confidence
        self.radar_sigma_high = radar_sigma_at_high_snr_m
        self.radar_sigma_low = radar_sigma_at_low_snr_m
        self.vision_sigma = vision_sigma_m
        self.no_vision_penalty = no_vision_penalty

    def _transform(self, point: RadarPoint) -> np.ndarray:
        p = np.array([point.x, point.y, point.z, 1.0], dtype=np.float64)
        return (self.transform @ p)[:3]

    def _radar_sigma(self, snr_db: float | None) -> float:
        if snr_db is None:
            return self.radar_sigma_low
        normalized = float(np.clip((snr_db - self.min_snr_db) / 24.0, 0.0, 1.0))
        return self.radar_sigma_low + normalized * (self.radar_sigma_high - self.radar_sigma_low)

    def fuse(
        self,
        radar: RadarFrame,
        vision: VisionFrame | None,
        *,
        radar_trust: float = 1.0,
        vision_trust: float = 1.0,
    ) -> list[FusedMeasurement]:
        tree = None
        vision_points = None
        if vision is not None and len(vision.points_xyz):
            vision_points = vision.points_xyz
            tree = cKDTree(vision_points)

        out: list[FusedMeasurement] = []
        radar_trust = float(np.clip(radar_trust, 0.0, 1.0))
        vision_trust = float(np.clip(vision_trust, 0.0, 1.0))

        for rp in radar.points:
            if rp.snr_db is not None and rp.snr_db < self.min_snr_db:
                continue

            radar_pos = self._transform(rp)
            sigma_r = self._radar_sigma(rp.snr_db)
            snr_score = 0.55 if rp.snr_db is None else float(
                np.clip((rp.snr_db - self.min_snr_db) / 20.0, 0.0, 1.0)
            )

            nearest_distance = None
            geometry_score = 0.0
            visibility_state = "radar_only"
            fused_pos = radar_pos
            sigma = sigma_r

            if tree is not None and vision_points is not None:
                dist, idx = tree.query(radar_pos, k=1)
                nearest_distance = float(dist)
                if nearest_distance <= self.max_pairing_distance_m:
                    visibility_state = "corroborated"
                    geometry_score = math.exp(
                        -0.5 * (nearest_distance / max(self.max_pairing_distance_m / 2.0, 1e-6)) ** 2
                    )
                    vision_pos = vision_points[int(idx)]
                    # Independent Gaussian measurement fusion.
                    wr = radar_trust / max(sigma_r**2, 1e-9)
                    wv = vision_trust / max(self.vision_sigma**2, 1e-9)
                    total = wr + wv
                    if total > 0:
                        fused_pos = (wr * radar_pos + wv * vision_pos) / total
                        sigma = math.sqrt(1.0 / total)
                else:
                    visibility_state = "uncorroborated_or_occluded"
                    geometry_score = 0.0

            trust_score = 0.65 * radar_trust + 0.35 * vision_trust
            confidence = 0.52 * snr_score + 0.28 * geometry_score + 0.20 * trust_score
            if tree is None:
                confidence *= self.no_vision_penalty
            confidence = float(np.clip(confidence, 0.0, 1.0))
            if confidence < self.min_confidence:
                continue

            cov = (sigma**2, sigma**2, sigma**2)
            out.append(
                FusedMeasurement(
                    position_xyz=tuple(float(x) for x in fused_pos),
                    covariance_diag_m2=cov,
                    radial_velocity_mps=float(rp.velocity),
                    snr_db=rp.snr_db,
                    nearest_depth_distance_m=nearest_distance,
                    confidence=confidence,
                    radar_trust=radar_trust,
                    vision_trust=vision_trust,
                    visibility_state=visibility_state,
                )
            )

        out.sort(key=lambda m: m.confidence, reverse=True)
        return out
