import numpy as np

from hybrid_scanner.fusion import FusionEngine
from hybrid_scanner.models import RadarFrame, RadarPoint, VisionFrame


def engine():
    return FusionEngine(
        radar_to_camera=np.eye(4).tolist(),
        max_pairing_distance_m=0.35,
        min_snr_db=6,
        min_confidence=0.2,
        radar_sigma_at_high_snr_m=0.03,
        radar_sigma_at_low_snr_m=0.2,
        vision_sigma_m=0.025,
        no_vision_penalty=0.82,
    )


def test_fusion_uses_near_depth_geometry():
    radar = RadarFrame(1, 100, [RadarPoint(0, 1, 0, 0, snr_db=20)])
    vision = VisionFrame(100, np.array([[0.01, 1.01, 0.0], [2, 2, 2]], dtype=float))
    out = engine().fuse(radar, vision)
    assert len(out) == 1
    assert out[0].nearest_depth_distance_m < 0.03
    assert out[0].confidence > 0.5


def test_zero_radar_trust_emits_nothing():
    radar = RadarFrame(1, 100, [RadarPoint(0, 1, 0, 0, snr_db=40)])
    vision = VisionFrame(100, np.array([[0.0, 1.0, 0.0]] * 10, dtype=float))
    assert engine().fuse(radar, vision, radar_trust=0.0, vision_trust=1.0) == []


def test_uncorroborated_measurement_is_penalized():
    radar = RadarFrame(1, 100, [RadarPoint(0, 1, 0, 0, snr_db=20)])
    vision = VisionFrame(100, np.array([[5.0, 5.0, 5.0]] * 10, dtype=float))
    out = engine().fuse(radar, vision)
    assert out
    assert out[0].visibility_state == "uncorroborated_or_occluded"
    assert out[0].confidence < 0.8
