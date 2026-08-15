from __future__ import annotations

from dataclasses import dataclass
import math
import time

from hybrid_scanner.models import TrackSnapshot


@dataclass
class _Voxel:
    log_odds: float
    last_seen_ns: int


class SparseOccupancyMap:
    """Small persistent evidence map for confirmed tracked targets.

    This is not a full SLAM map. It is intentionally a bounded, decaying scene
    memory used for product UX, persistence, and active-scan guidance.
    """

    def __init__(
        self,
        *,
        voxel_size_m: float,
        hit_log_odds: float,
        decay_per_s: float,
        prune_below: float,
        max_voxels: int,
    ) -> None:
        self.voxel_size_m = voxel_size_m
        self.hit_log_odds = hit_log_odds
        self.decay_per_s = decay_per_s
        self.prune_below = prune_below
        self.max_voxels = max_voxels
        self._voxels: dict[tuple[int, int, int], _Voxel] = {}
        self._last_prune_ns = time.monotonic_ns()

    def _key(self, p: tuple[float, float, float]) -> tuple[int, int, int]:
        return tuple(int(math.floor(v / self.voxel_size_m)) for v in p)

    def update(self, tracks: list[TrackSnapshot], now_ns: int) -> None:
        for track in tracks:
            if not track.confirmed:
                continue
            key = self._key(track.position_xyz)
            voxel = self._voxels.get(key)
            delta = self.hit_log_odds * track.confidence
            if voxel is None:
                self._voxels[key] = _Voxel(log_odds=delta, last_seen_ns=now_ns)
            else:
                dt = max(0.0, (now_ns - voxel.last_seen_ns) / 1e9)
                voxel.log_odds = max(0.0, voxel.log_odds - self.decay_per_s * dt) + delta
                voxel.last_seen_ns = now_ns

        if now_ns - self._last_prune_ns > 2_000_000_000 or len(self._voxels) > self.max_voxels:
            self._prune(now_ns)

    def _prune(self, now_ns: int) -> None:
        scored: list[tuple[float, tuple[int, int, int]]] = []
        for key, voxel in list(self._voxels.items()):
            dt = max(0.0, (now_ns - voxel.last_seen_ns) / 1e9)
            score = max(0.0, voxel.log_odds - self.decay_per_s * dt)
            if score < self.prune_below:
                self._voxels.pop(key, None)
            else:
                voxel.log_odds = score
                voxel.last_seen_ns = now_ns
                scored.append((score, key))

        if len(self._voxels) > self.max_voxels:
            scored.sort(reverse=True)
            keep = {key for _, key in scored[: self.max_voxels]}
            self._voxels = {k: v for k, v in self._voxels.items() if k in keep}
        self._last_prune_ns = now_ns

    def occupancy_score_near(self, point: tuple[float, float, float]) -> float:
        voxel = self._voxels.get(self._key(point))
        return 0.0 if voxel is None else voxel.log_odds

    def top_voxels(self, limit: int = 200) -> list[dict]:
        items = sorted(self._voxels.items(), key=lambda kv: kv[1].log_odds, reverse=True)[:limit]
        out = []
        for key, voxel in items:
            center = tuple((k + 0.5) * self.voxel_size_m for k in key)
            out.append({"center_xyz": center, "evidence": voxel.log_odds})
        return out
