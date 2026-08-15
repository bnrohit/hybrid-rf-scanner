from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from hybrid_scanner.models import FusedMeasurement, TrackSnapshot


@dataclass
class _Track:
    track_id: int
    x: np.ndarray
    p: np.ndarray
    created_ns: int
    last_ns: int
    hits: int = 1
    misses: int = 0
    confidence: float = 0.5


class MultiTargetTracker:
    """Constant-velocity Kalman tracker with global assignment."""

    def __init__(
        self,
        *,
        association_gate_m: float,
        confirmation_hits: int,
        max_misses: int,
        process_noise: float,
        default_measurement_sigma_m: float,
    ) -> None:
        self.gate = association_gate_m
        self.confirmation_hits = confirmation_hits
        self.max_misses = max_misses
        self.process_noise = process_noise
        self.default_measurement_sigma_m = default_measurement_sigma_m
        self._tracks: list[_Track] = []
        self._next_id = 1

    def _predict(self, track: _Track, timestamp_ns: int) -> None:
        dt = max(0.0, min((timestamp_ns - track.last_ns) / 1e9, 2.0))
        f = np.eye(6)
        f[0, 3] = dt
        f[1, 4] = dt
        f[2, 5] = dt
        q = self.process_noise
        qmat = np.eye(6) * q * max(dt, 1e-3)
        track.x = f @ track.x
        track.p = f @ track.p @ f.T + qmat
        track.last_ns = timestamp_ns

    def _new_track(self, m: FusedMeasurement, timestamp_ns: int) -> None:
        pos = np.asarray(m.position_xyz, dtype=np.float64)
        x = np.zeros(6, dtype=np.float64)
        x[:3] = pos
        sigma2 = float(np.mean(m.covariance_diag_m2))
        p = np.diag([sigma2, sigma2, sigma2, 1.0, 1.0, 1.0])
        self._tracks.append(
            _Track(
                track_id=self._next_id,
                x=x,
                p=p,
                created_ns=timestamp_ns,
                last_ns=timestamp_ns,
                confidence=m.confidence,
            )
        )
        self._next_id += 1

    def _update_track(self, track: _Track, m: FusedMeasurement) -> None:
        z = np.asarray(m.position_xyz, dtype=np.float64)
        h = np.zeros((3, 6))
        h[:, :3] = np.eye(3)
        r = np.diag(np.maximum(np.asarray(m.covariance_diag_m2), 1e-6))
        innovation = z - h @ track.x
        s = h @ track.p @ h.T + r
        k = track.p @ h.T @ np.linalg.pinv(s)
        track.x = track.x + k @ innovation
        i = np.eye(6)
        track.p = (i - k @ h) @ track.p
        track.hits += 1
        track.misses = 0
        track.confidence = float(np.clip(0.70 * track.confidence + 0.30 * m.confidence, 0, 1))

    def update(self, measurements: list[FusedMeasurement], timestamp_ns: int) -> list[TrackSnapshot]:
        for track in self._tracks:
            self._predict(track, timestamp_ns)

        assigned_tracks: set[int] = set()
        assigned_measurements: set[int] = set()

        if self._tracks and measurements:
            cost = np.full((len(self._tracks), len(measurements)), 1e6, dtype=np.float64)
            for ti, track in enumerate(self._tracks):
                for mi, m in enumerate(measurements):
                    distance = float(np.linalg.norm(track.x[:3] - np.asarray(m.position_xyz)))
                    if distance <= self.gate:
                        cost[ti, mi] = distance

            rows, cols = linear_sum_assignment(cost)
            for ti, mi in zip(rows, cols):
                if cost[ti, mi] > self.gate:
                    continue
                self._update_track(self._tracks[ti], measurements[mi])
                assigned_tracks.add(ti)
                assigned_measurements.add(mi)

        for ti, track in enumerate(self._tracks):
            if ti not in assigned_tracks:
                track.misses += 1
                track.confidence *= 0.92

        for mi, measurement in enumerate(measurements):
            if mi not in assigned_measurements:
                self._new_track(measurement, timestamp_ns)

        self._tracks = [t for t in self._tracks if t.misses <= self.max_misses]
        return self.snapshots(timestamp_ns)

    def snapshots(self, now_ns: int) -> list[TrackSnapshot]:
        snapshots = []
        for t in self._tracks:
            diag = np.diag(t.p)
            snapshots.append(
                TrackSnapshot(
                    track_id=t.track_id,
                    position_xyz=tuple(float(v) for v in t.x[:3]),
                    velocity_xyz_mps=tuple(float(v) for v in t.x[3:]),
                    covariance_diag=tuple(float(v) for v in diag),
                    confidence=float(np.clip(t.confidence, 0, 1)),
                    hits=t.hits,
                    misses=t.misses,
                    confirmed=t.hits >= self.confirmation_hits,
                    age_s=max(0.0, (now_ns - t.created_ns) / 1e9),
                )
            )
        snapshots.sort(key=lambda s: (not s.confirmed, -s.confidence, s.track_id))
        return snapshots
