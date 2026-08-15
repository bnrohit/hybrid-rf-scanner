from __future__ import annotations

from collections import deque

import numpy as np

from hybrid_scanner.models import FusedMeasurement


class CalibrationDriftMonitor:
    """Robustly watches radar↔depth spatial residuals for mount/calibration drift."""

    def __init__(
        self,
        *,
        window_size: int,
        min_samples: int,
        median_warn_m: float,
        p95_warn_m: float,
    ) -> None:
        self.samples: deque[float] = deque(maxlen=window_size)
        self.min_samples = min_samples
        self.median_warn_m = median_warn_m
        self.p95_warn_m = p95_warn_m

    def update(self, measurements: list[FusedMeasurement]) -> None:
        for m in measurements:
            if m.nearest_depth_distance_m is not None:
                self.samples.append(float(m.nearest_depth_distance_m))

    def snapshot(self) -> dict:
        if not self.samples:
            return {
                "samples": 0,
                "median_residual_m": None,
                "p95_residual_m": None,
                "degraded": False,
                "reason": "insufficient_samples",
            }
        arr = np.asarray(self.samples, dtype=np.float64)
        median = float(np.median(arr))
        p95 = float(np.percentile(arr, 95))
        enough = len(arr) >= self.min_samples
        degraded = enough and (median > self.median_warn_m or p95 > self.p95_warn_m)
        return {
            "samples": len(arr),
            "median_residual_m": median,
            "p95_residual_m": p95,
            "degraded": degraded,
            "reason": "residual_threshold_exceeded" if degraded else ("ok" if enough else "insufficient_samples"),
        }
