from __future__ import annotations

import signal
import threading
import time

from loguru import logger
import uvicorn

from hybrid_scanner.api import FRAMES, LOOP_LATENCY, MEASUREMENTS, SYNC_SKEW, TRACKS, build_app
from hybrid_scanner.calibration_monitor import CalibrationDriftMonitor
from hybrid_scanner.config import ScannerConfig
from hybrid_scanner.fusion import FusionEngine
from hybrid_scanner.guidance import ActiveScanAdvisor
from hybrid_scanner.health import HealthMonitor
from hybrid_scanner.mapping import SparseOccupancyMap
from hybrid_scanner.radar.ti_iwr6843 import TiIwr6843
from hybrid_scanner.recording import JsonlRecorder
from hybrid_scanner.simulation import Simulator
from hybrid_scanner.state import StatusStore
from hybrid_scanner.sync import FrameBus
from hybrid_scanner.tracking import MultiTargetTracker
from hybrid_scanner.vision.realsense import RealSenseD435i
from hybrid_scanner.workers import ReconnectingWorker


class ScannerEngine:
    def __init__(
        self,
        cfg: ScannerConfig,
        *,
        mode: str = "fused",
        simulation: bool = False,
        api_enabled: bool = False,
    ) -> None:
        self.cfg = cfg
        self.mode = mode
        self.simulation = simulation
        self.api_enabled = api_enabled
        self.store = StatusStore()
        self.store.update(mode="simulation" if simulation else mode)
        self.stop_event = threading.Event()

        self.bus = FrameBus(cfg.sync.buffer_size)
        self.health = HealthMonitor(cfg.sync.stale_sensor_ms)
        self.fusion = FusionEngine(
            radar_to_camera=cfg.fusion.radar_to_camera,
            max_pairing_distance_m=cfg.fusion.max_pairing_distance_m,
            min_snr_db=cfg.fusion.min_snr_db,
            min_confidence=cfg.fusion.min_confidence,
            radar_sigma_at_high_snr_m=cfg.fusion.radar_sigma_at_high_snr_m,
            radar_sigma_at_low_snr_m=cfg.fusion.radar_sigma_at_low_snr_m,
            vision_sigma_m=cfg.fusion.vision_sigma_m,
            no_vision_penalty=cfg.fusion.no_vision_penalty,
        )
        cm = cfg.calibration_monitor
        self.calibration_monitor = CalibrationDriftMonitor(
            window_size=cm.window_size,
            min_samples=cm.min_samples,
            median_warn_m=cm.median_warn_m,
            p95_warn_m=cm.p95_warn_m,
        )
        self.tracker = MultiTargetTracker(
            association_gate_m=cfg.tracker.association_gate_m,
            confirmation_hits=cfg.tracker.confirmation_hits,
            max_misses=cfg.tracker.max_misses,
            process_noise=cfg.tracker.process_noise,
            default_measurement_sigma_m=cfg.tracker.default_measurement_sigma_m,
        )
        self.scene_map = SparseOccupancyMap(
            voxel_size_m=cfg.mapping.voxel_size_m,
            hit_log_odds=cfg.mapping.hit_log_odds,
            decay_per_s=cfg.mapping.decay_per_s,
            prune_below=cfg.mapping.prune_below,
            max_voxels=cfg.mapping.max_voxels,
        )
        self.advisor = ActiveScanAdvisor()
        self.recorder = (
            JsonlRecorder(cfg.app.recording_path, cfg.app.recording_queue_size)
            if cfg.app.recording_enabled
            else None
        )
        self.sim = Simulator() if simulation else None
        self.radar = None
        self.vision = None
        self.workers: list[ReconnectingWorker] = []
        self.api_thread = None

    def _start_api(self) -> None:
        app = build_app(
            self.store,
            token=self.cfg.api.token(),
            host=self.cfg.api.host,
            allow_loopback_without_token=self.cfg.api.allow_unauthenticated_loopback,
        )

        def serve() -> None:
            uvicorn.run(app, host=self.cfg.api.host, port=self.cfg.api.port, log_level="warning")

        self.api_thread = threading.Thread(target=serve, daemon=True, name="api-server")
        self.api_thread.start()
        logger.info("API listening on {}:{}", self.cfg.api.host, self.cfg.api.port)

    def _build_hardware(self) -> None:
        if self.mode == "fused" and not self.cfg.fusion.calibration_validated:
            raise RuntimeError(
                "fused hardware mode is blocked because calibration_validated=false; "
                "run scripts/calibrate_from_csv.py and validate the mount first"
            )
        if self.mode in {"fused", "radar-only"}:
            if not self.cfg.radar.enabled:
                raise RuntimeError("radar is disabled in configuration for a mode that requires it")
            r = self.cfg.radar
            self.radar = TiIwr6843(
                config_port=r.config_port,
                data_port=r.data_port,
                profile_path=r.profile_path,
                config_baud=r.config_baud,
                data_baud=r.data_baud,
                read_timeout_s=r.read_timeout_s,
                cli_response_timeout_s=r.cli_response_timeout_s,
                tlv_length_mode=r.tlv_length_mode,
                max_packet_bytes=r.max_packet_bytes,
                max_coordinate_m=r.max_coordinate_m,
            )
            self.workers.append(
                ReconnectingWorker(
                    name="radar",
                    connect=self.radar.connect,
                    disconnect=self.radar.disconnect,
                    read=self.radar.read_frame,
                    publish=self.bus.add_radar,
                    health=self.health,
                    initial_backoff_s=r.reconnect_initial_s,
                    max_backoff_s=r.reconnect_max_s,
                )
            )

        if self.mode in {"fused", "vision-only"}:
            if not self.cfg.vision.enabled:
                raise RuntimeError("vision is disabled in configuration for a mode that requires it")
            v = self.cfg.vision
            self.vision = RealSenseD435i(
                serial_number=v.serial_number,
                width=v.width,
                height=v.height,
                fps=v.fps,
                timeout_ms=v.timeout_ms,
                max_points=v.max_points,
                min_depth_m=v.min_depth_m,
                max_depth_m=v.max_depth_m,
            )
            self.workers.append(
                ReconnectingWorker(
                    name="vision",
                    connect=self.vision.connect,
                    disconnect=self.vision.disconnect,
                    read=self.vision.read_frame,
                    publish=self.bus.add_vision,
                    health=self.health,
                    initial_backoff_s=v.reconnect_initial_s,
                    max_backoff_s=v.reconnect_max_s,
                )
            )

    def _signal_handler(self, *_args) -> None:
        self.stop_event.set()

    def _ready(self, sensors: dict) -> bool:
        if self.simulation:
            return True
        if self.mode == "radar-only":
            return not sensors["radar"]["stale"]
        if self.mode == "vision-only":
            return not sensors["vision"]["stale"]
        return not sensors["radar"]["stale"] and not sensors["vision"]["stale"]

    def _record_event(self, radar, vision, measurements, tracks, guidance, skew_ms) -> None:
        if not self.recorder:
            return
        event = {
            "schema": "hybrid-rf-scanner.event.v2",
            "node_id": self.cfg.app.node_id,
            "timestamp_epoch_s": time.time(),
            "radar": {
                "frame_number": radar.frame_number,
                "timestamp_ns": radar.timestamp_ns,
                "points": [p.to_dict() for p in radar.points],
                "warnings": radar.parser_warnings,
            },
            "vision": None if vision is None else {
                "timestamp_ns": vision.timestamp_ns,
                "point_count": len(vision.points_xyz),
                "device_timestamp_ms": vision.device_timestamp_ms,
            },
            "sync_skew_ms": skew_ms,
            "measurements": [m.to_dict() for m in measurements],
            "tracks": [t.to_dict() for t in tracks],
            "guidance": guidance.to_dict() if guidance else None,
        }
        self.recorder.submit(event)

    def run_forever(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._signal_handler)
            except ValueError:
                pass

        if self.api_enabled:
            self._start_api()

        if not self.simulation:
            self._build_hardware()
            for worker in self.workers:
                worker.start()

        period = 1.0 / self.cfg.app.loop_hz
        last_frame_number = -1
        logger.info("Scanner started in {} mode", "simulation" if self.simulation else self.mode)

        try:
            while not self.stop_event.is_set():
                started = time.monotonic()
                now_ns = time.monotonic_ns()

                if self.simulation:
                    radar, vision = self.sim.next()
                    self.health.frame("radar", radar.timestamp_ns)
                    self.health.frame("vision", vision.timestamp_ns)
                    skew_ms = abs(radar.timestamp_ns - vision.timestamp_ns) / 1e6
                elif self.mode == "vision-only":
                    # Vision-only mode is a hardware diagnostics mode; there is no radar measurement to fuse.
                    sensors = self.health.snapshot(now_ns)
                    self.store.update(
                        healthy=not sensors["vision"]["stale"],
                        ready=self._ready(sensors),
                        sensors=sensors,
                        measurements=[],
                        tracks=[],
                    )
                    self.stop_event.wait(period)
                    continue
                else:
                    radar = self.bus.latest_radar_after(last_frame_number)
                    if radar is None:
                        sensors = self.health.snapshot(now_ns)
                        self.store.update(
                            healthy=self._ready(sensors),
                            ready=self._ready(sensors),
                            sensors=sensors,
                        )
                        self.stop_event.wait(min(period, 0.02))
                        continue
                    if self.mode == "fused":
                        vision, skew_ms = self.bus.nearest_vision(radar.timestamp_ns, self.cfg.sync.max_skew_ms)
                    else:
                        vision, skew_ms = None, None

                last_frame_number = radar.frame_number
                radar_trust = self.health.trust("radar", now_ns)
                vision_trust = 0.0 if self.mode == "radar-only" else self.health.trust("vision", now_ns)
                measurements = self.fusion.fuse(
                    radar,
                    vision,
                    radar_trust=radar_trust,
                    vision_trust=vision_trust,
                )
                if self.cfg.calibration_monitor.enabled and vision is not None:
                    self.calibration_monitor.update(measurements)
                calibration = self.calibration_monitor.snapshot()
                tracks = self.tracker.update(measurements, radar.timestamp_ns)
                if self.cfg.mapping.enabled:
                    self.scene_map.update(tracks, now_ns)
                guidance = (
                    self.advisor.recommend(tracks, self.scene_map)
                    if self.cfg.research.active_scan_guidance
                    else None
                )

                sensors = self.health.snapshot(now_ns)
                ready = self._ready(sensors)
                if self.cfg.calibration_monitor.fail_readiness_on_drift and calibration["degraded"]:
                    ready = False
                self.store.update(
                    healthy=ready,
                    ready=ready,
                    calibration=calibration,
                    frame_number=radar.frame_number,
                    sync_skew_ms=skew_ms,
                    measurements=[m.to_dict() for m in measurements[:50]],
                    tracks=[t.to_dict() for t in tracks[:50]],
                    guidance=guidance.to_dict() if guidance else None,
                    sensors=sensors,
                    last_error=None,
                    recorder_dropped=0 if self.recorder is None else self.recorder.dropped,
                )

                FRAMES.inc()
                MEASUREMENTS.set(len(measurements))
                TRACKS.set(len(tracks))
                if skew_ms is not None:
                    SYNC_SKEW.set(skew_ms)
                self._record_event(radar, vision, measurements, tracks, guidance, skew_ms)

                elapsed = time.monotonic() - started
                LOOP_LATENCY.observe(elapsed)
                remaining = period - elapsed
                if remaining > 0:
                    self.stop_event.wait(remaining)

        except Exception as exc:
            self.store.update(healthy=False, ready=False, last_error=str(exc))
            logger.exception("Scanner failed: {}", exc)
            raise
        finally:
            self.stop_event.set()
            for worker in self.workers:
                worker.stop()
            if self.recorder:
                self.recorder.close()
            logger.info("Scanner stopped")
