# Line-by-Line Structural Audit - v2.0.1

Generated from the corrected source tree. Every production Python file parses successfully. Top-level executable blocks are indexed by exact final line range.

- `src/hybrid_scanner/__init__.py` (1 lines): 1-1 module init/config
- `src/hybrid_scanner/api.py` (118 lines): 15-15 module init/config; 16-16 module init/config; 17-17 module init/config; 18-18 module init/config; 19-23 module init/config; 24-24 module init/config; 27-33 fn _is_loopback; 36-118 fn build_app
- `src/hybrid_scanner/calibration_monitor.py` (51 lines): 10-51 class CalibrationDriftMonitor
- `src/hybrid_scanner/cli.py` (105 lines): 15-15 module init/config; 19-72 fn doctor; 76-96 fn run; 100-101 fn version; 104-105 module init/config
- `src/hybrid_scanner/config.py` (198 lines): 13-23 class AppConfig; 26-46 class RadarConfig; 49-68 class VisionConfig; 71-74 class SyncConfig; 77-113 class FusionConfig; 116-128 class CalibrationMonitorConfig; 131-137 class TrackerConfig; 140-146 class MapConfig; 149-156 class ApiConfig; 159-163 class ResearchConfig; 166-176 class ScannerConfig; 179-198 fn load_config
- `src/hybrid_scanner/engine.py` (378 lines): 27-378 class ScannerEngine
- `src/hybrid_scanner/fusion.py` (149 lines): 11-149 class FusionEngine
- `src/hybrid_scanner/guidance.py` (65 lines): 9-65 class ActiveScanAdvisor
- `src/hybrid_scanner/health.py` (70 lines): 10-15 class _SensorHealth; 18-70 class HealthMonitor
- `src/hybrid_scanner/mapping.py` (88 lines): 11-13 class _Voxel; 16-88 class SparseOccupancyMap
- `src/hybrid_scanner/models.py` (95 lines): 9-10 fn _finite_vec3; 14-27 class RadarPoint; 31-35 class RadarFrame; 39-44 class VisionFrame; 48-67 class FusedMeasurement; 71-83 class TrackSnapshot; 87-95 class ScanGuidance
- `src/hybrid_scanner/radar/__init__.py` (0 lines): package marker only
- `src/hybrid_scanner/radar/ti_iwr6843.py` (335 lines): 10-13 module init/config; 18-18 module init/config; 19-19 module init/config; 20-20 module init/config; 21-21 module init/config; 22-22 module init/config; 25-185 class TiPacketParser; 188-335 class TiIwr6843
- `src/hybrid_scanner/recording.py` (81 lines): 9-81 class JsonlRecorder
- `src/hybrid_scanner/simulation.py` (57 lines): 11-57 class Simulator
- `src/hybrid_scanner/state.py` (39 lines): 9-39 class StatusStore
- `src/hybrid_scanner/sync.py` (64 lines): 9-64 class FrameBus
- `src/hybrid_scanner/tracking.py` (145 lines): 12-20 class _Track; 23-145 class MultiTargetTracker
- `src/hybrid_scanner/vision/__init__.py` (0 lines): package marker only
- `src/hybrid_scanner/vision/realsense.py` (139 lines): 11-139 class RealSenseD435i
- `src/hybrid_scanner/workers.py` (71 lines): 11-71 class ReconnectingWorker
- `scripts/calibrate_from_csv.py` (86 lines): 12-42 fn rigid_transform; 45-50 fn atomic_yaml_write; 53-82 fn main; 85-86 module init/config
- `scripts/generate_release_manifest.py` (75 lines): 11-14 module init/config; 15-15 module init/config; 16-20 module init/config; 23-28 fn sha256; 31-39 fn include_file; 42-71 fn main; 74-75 module init/config

Infrastructure reviewed: CI workflow, Dockerfile/Compose, systemd unit, pyproject, scanner config.

Result: **20/20 local regression tests passed after corrections.** GitHub CI repeats compile, lint, tests/coverage, package build, dependency consistency, and dependency audit.
