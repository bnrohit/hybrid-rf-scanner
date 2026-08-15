from __future__ import annotations

import numpy as np

from hybrid_scanner.mapping import SparseOccupancyMap
from hybrid_scanner.models import ScanGuidance, TrackSnapshot


class ActiveScanAdvisor:
    """Advisory next-best-view heuristic for uncertain confirmed tracks.

    This does not drive motors or autonomously move hardware. It only returns a
    suggested operator motion designed to increase viewpoint diversity.
    """

    CANDIDATES = {
        "move_left": np.array([-1.0, 0.0, 0.0]),
        "move_right": np.array([1.0, 0.0, 0.0]),
        "move_up": np.array([0.0, 0.0, 1.0]),
        "move_down": np.array([0.0, 0.0, -1.0]),
        "move_back": np.array([0.0, -1.0, 0.0]),
    }

    def recommend(self, tracks: list[TrackSnapshot], scene_map: SparseOccupancyMap) -> ScanGuidance:
        confirmed = [t for t in tracks if t.confirmed]
        if not confirmed:
            return ScanGuidance(
                action="hold",
                direction_xyz=(0.0, 0.0, 0.0),
                reason="No confirmed target needs another viewpoint.",
            )

        target = max(confirmed, key=lambda t: sum(t.covariance_diag[:3]))
        p = np.asarray(target.position_xyz, dtype=np.float64)
        distance = float(np.linalg.norm(p))
        if distance < 1e-6:
            return ScanGuidance("hold", (0.0, 0.0, 0.0), "Target is at sensor origin.")

        los = p / distance
        uncertainty = float(np.sqrt(max(sum(target.covariance_diag[:3]), 0.0)))
        best = None
        for action, direction in self.CANDIDATES.items():
            parallax = float(np.linalg.norm(np.cross(direction, los)))
            candidate_point = tuple(float(v) for v in (direction * 0.35))
            occupancy_penalty = min(scene_map.occupancy_score_near(candidate_point), 3.0) / 3.0
            gain = uncertainty * parallax * (1.0 - 0.45 * occupancy_penalty)
            if best is None or gain > best[0]:
                best = (gain, action, direction)

        gain, action, direction = best
        if gain < 0.02:
            return ScanGuidance(
                action="hold",
                direction_xyz=(0.0, 0.0, 0.0),
                reason="Current track uncertainty is already low.",
                target_track_id=target.track_id,
                expected_information_gain=gain,
            )
        return ScanGuidance(
            action=action,
            direction_xyz=tuple(float(v) for v in direction),
            reason="Increase parallax on the most uncertain confirmed track.",
            target_track_id=target.track_id,
            expected_information_gain=gain,
        )
