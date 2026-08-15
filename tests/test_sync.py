import numpy as np

from hybrid_scanner.models import RadarFrame, VisionFrame
from hybrid_scanner.sync import FrameBus


def test_nearest_vision_respects_skew():
    bus = FrameBus(10)
    bus.add_vision(VisionFrame(timestamp_ns=1_040_000_000, points_xyz=np.zeros((1, 3))))
    vision, skew = bus.nearest_vision(1_000_000_000, 60)
    assert vision is not None
    assert skew == 40.0
    vision, skew = bus.nearest_vision(1_000_000_000, 20)
    assert vision is None
    assert skew == 40.0


def test_latest_radar_is_not_replayed():
    bus = FrameBus(10)
    frame = RadarFrame(frame_number=7, timestamp_ns=123, points=[])
    bus.add_radar(frame)
    assert bus.latest_radar_after(-1) is frame
    assert bus.latest_radar_after(7) is None
