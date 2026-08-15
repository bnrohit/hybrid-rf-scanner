from __future__ import annotations

import time

import numpy as np
from loguru import logger

from hybrid_scanner.models import VisionFrame


class RealSenseD435i:
    def __init__(
        self,
        *,
        serial_number: str | None,
        width: int,
        height: int,
        fps: int,
        timeout_ms: int,
        max_points: int,
        min_depth_m: float,
        max_depth_m: float,
    ) -> None:
        self.serial_number = serial_number
        self.width = width
        self.height = height
        self.fps = fps
        self.timeout_ms = timeout_ms
        self.max_points = max_points
        self.min_depth_m = min_depth_m
        self.max_depth_m = max_depth_m
        self.rs = None
        self.pipeline = None
        self.pc = None
        self.profile = None
        self.device_info: dict[str, str] = {}

    def connect(self) -> None:
        try:
            import pyrealsense2 as rs
        except ImportError as exc:
            raise RuntimeError(
                "pyrealsense2 is not installed. Install a librealsense build compatible "
                "with this host, then install requirements-hardware.txt."
            ) from exc

        self.rs = rs
        self.pipeline = rs.pipeline()
        cfg = rs.config()
        if self.serial_number:
            cfg.enable_device(self.serial_number)

        cfg.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
        cfg.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        cfg.enable_stream(rs.stream.accel, rs.format.motion_xyz32f, 63)
        cfg.enable_stream(rs.stream.gyro, rs.format.motion_xyz32f, 200)

        self.profile = self.pipeline.start(cfg)
        self.pc = rs.pointcloud()
        device = self.profile.get_device()
        for key, option in [
            ("name", rs.camera_info.name),
            ("serial", rs.camera_info.serial_number),
            ("firmware", rs.camera_info.firmware_version),
        ]:
            try:
                self.device_info[key] = device.get_info(option)
            except Exception:
                pass
        logger.info("RealSense started: {}", self.device_info or "device info unavailable")

    def disconnect(self) -> None:
        if self.pipeline:
            try:
                self.pipeline.stop()
            finally:
                self.pipeline = None
                self.profile = None
                self.pc = None

    @staticmethod
    def _motion_xyz(frame) -> np.ndarray:
        data = frame.as_motion_frame().get_motion_data()
        return np.array([data.x, data.y, data.z], dtype=np.float64)

    def read_frame(self) -> VisionFrame | None:
        if not self.pipeline or not self.rs or not self.pc:
            raise RuntimeError("RealSense is not connected")

        try:
            frames = self.pipeline.wait_for_frames(self.timeout_ms)
        except RuntimeError as exc:
            raise RuntimeError(f"RealSense frame timeout/disconnect: {exc}") from exc

        captured_ns = time.monotonic_ns()
        depth = frames.get_depth_frame()
        if not depth:
            return None

        points = self.pc.calculate(depth)
        vertices = np.asanyarray(points.get_vertices())
        xyz = vertices.view(np.float32).reshape(-1, 3).astype(np.float64, copy=False)

        finite = np.isfinite(xyz).all(axis=1)
        z = xyz[:, 2]
        in_range = (z >= self.min_depth_m) & (z <= self.max_depth_m)
        xyz = xyz[finite & in_range]

        if len(xyz) > self.max_points:
            # Deterministic stride sampling avoids allocating random index arrays every frame.
            step = max(1, len(xyz) // self.max_points)
            xyz = xyz[::step][: self.max_points]

        accel = None
        gyro = None
        try:
            for frame in frames:
                profile = frame.get_profile()
                stream_type = profile.stream_type()
                if stream_type == self.rs.stream.accel:
                    accel = self._motion_xyz(frame)
                elif stream_type == self.rs.stream.gyro:
                    gyro = self._motion_xyz(frame)
        except Exception:
            logger.debug("Motion sample not available in this frameset")

        device_timestamp_ms = None
        try:
            device_timestamp_ms = float(depth.get_timestamp())
        except Exception:
            pass

        return VisionFrame(
            timestamp_ns=captured_ns,
            points_xyz=xyz,
            gyro_xyz=gyro,
            accel_xyz=accel,
            device_timestamp_ms=device_timestamp_ms,
        )
