from hybrid_scanner.guidance import ActiveScanAdvisor
from hybrid_scanner.mapping import SparseOccupancyMap
from hybrid_scanner.models import TrackSnapshot


def test_guidance_returns_advisory_motion():
    scene = SparseOccupancyMap(
        voxel_size_m=0.1,
        hit_log_odds=0.8,
        decay_per_s=0.01,
        prune_below=0.05,
        max_voxels=1000,
    )
    track = TrackSnapshot(
        track_id=1,
        position_xyz=(0.2, 2.0, 0.1),
        velocity_xyz_mps=(0, 0, 0),
        covariance_diag=(0.2, 0.2, 0.2, 1, 1, 1),
        confidence=0.9,
        hits=5,
        misses=0,
        confirmed=True,
        age_s=1.0,
    )
    guidance = ActiveScanAdvisor().recommend([track], scene)
    assert guidance.action != "hold"
    assert guidance.target_track_id == 1
