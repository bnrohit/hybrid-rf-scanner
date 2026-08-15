from __future__ import annotations

import math
import time

import numpy as np

from hybrid_scanner.models import RadarFrame, RadarPoint, VisionFrame


class Simulator:
    def __init__(self, seed: int = 7) -> None:
        self.start_ns = time.monotonic_ns()
        self.frame = 0
        self.rng = np.random.default_rng(seed)

    def next(self) -> tuple[RadarFrame, VisionFrame]:
        self.frame += 1
        now_ns = time.monotonic_ns()
        t = (now_ns - self.start_ns) / 1e9

        targets = [
            np.array([0.45 * math.sin(t * 0.55), 1.6 + 0.12 * math.cos(t * 0.25), 0.20]),
            np.array([-0.55, 2.35 + 0.15 * math.sin(t * 0.35), -0.10]),
        ]

        radar_points = []
        clouds = []
        for idx, target in enumerate(targets):
            noisy = target + self.rng.normal(0, 0.018 + idx * 0.004, 3)
            radar_points.append(
                RadarPoint(
                    x=float(noisy[0]),
                    y=float(noisy[1]),
                    z=float(noisy[2]),
                    velocity=float(0.18 * math.cos(t * (0.55 if idx == 0 else 0.35))),
                    snr_db=float(19 - idx * 3 + self.rng.normal(0, 0.8)),
                    noise_db=4.0,
                )
            )
            clouds.append(target + self.rng.normal(0, 0.035, size=(2200, 3)))

        background = np.column_stack(
            [
                self.rng.uniform(-2.5, 2.5, 3000),
                self.rng.uniform(0.4, 5.0, 3000),
                self.rng.uniform(-1.2, 1.2, 3000),
            ]
        )
        vision = VisionFrame(
            timestamp_ns=now_ns + int(self.rng.normal(0, 4e6)),
            points_xyz=np.vstack([*clouds, background]),
            gyro_xyz=np.array([0.0, 0.0, 0.015]),
            accel_xyz=np.array([0.0, 0.0, 9.81]),
        )
        radar = RadarFrame(frame_number=self.frame, timestamp_ns=now_ns, points=radar_points)
        return radar, vision
