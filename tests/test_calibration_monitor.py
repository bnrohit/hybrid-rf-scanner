from hybrid_scanner.calibration_monitor import CalibrationDriftMonitor
from hybrid_scanner.models import FusedMeasurement


def m(distance):
    return FusedMeasurement(
        position_xyz=(0, 1, 0),
        covariance_diag_m2=(0.01, 0.01, 0.01),
        radial_velocity_mps=0,
        snr_db=20,
        nearest_depth_distance_m=distance,
        confidence=0.9,
        radar_trust=1,
        vision_trust=1,
    )


def test_calibration_drift_flag():
    monitor = CalibrationDriftMonitor(window_size=50, min_samples=5, median_warn_m=0.12, p95_warn_m=0.25)
    monitor.update([m(0.3) for _ in range(6)])
    assert monitor.snapshot()["degraded"] is True
