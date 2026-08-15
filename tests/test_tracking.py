from hybrid_scanner.models import FusedMeasurement
from hybrid_scanner.tracking import MultiTargetTracker


def measurement(x):
    return FusedMeasurement(
        position_xyz=(x, 1.0, 0.0),
        covariance_diag_m2=(0.01, 0.01, 0.01),
        radial_velocity_mps=0.0,
        snr_db=18.0,
        nearest_depth_distance_m=0.02,
        confidence=0.9,
        radar_trust=1.0,
        vision_trust=1.0,
    )


def test_track_id_persists_and_confirms():
    tracker = MultiTargetTracker(
        association_gate_m=0.5,
        confirmation_hits=3,
        max_misses=4,
        process_noise=0.1,
        default_measurement_sigma_m=0.1,
    )
    ids = []
    for i in range(3):
        snaps = tracker.update([measurement(i * 0.03)], 1_000_000_000 + i * 50_000_000)
        ids.append(snaps[0].track_id)
    assert len(set(ids)) == 1
    assert snaps[0].confirmed
