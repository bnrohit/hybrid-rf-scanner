# Line-by-Line Structural Audit

This file is the audit index for the final v2 source tree. Every production Python source file was parsed/compiled and manually reviewed as part of the rewrite. Rather than duplicating thousands of source lines here, each contiguous top-level code block is indexed by its exact final line range and purpose.

## `src/hybrid_scanner/__init__.py` — 1 lines

Package version is explicit and release-visible.

| Lines | Block |
|---:|---|
| 1–1 | module metadata/setup |

## `src/hybrid_scanner/models.py` — 95 lines

Data contracts audited for bounded, JSON-safe product state; NumPy is confined to internal geometry fields.

| Lines | Block |
|---:|---|
| 1–8 | module imports, constants, and module-level setup |
| 9–10 | function `_finite_vec3` |
| 14–27 | class `RadarPoint` |
| 31–35 | class `RadarFrame` |
| 39–44 | class `VisionFrame` |
| 48–67 | class `FusedMeasurement` |
| 71–83 | class `TrackSnapshot` |
| 87–95 | class `ScanGuidance` |

## `src/hybrid_scanner/config.py` — 166 lines

All externally tunable parameters are bounded; rigid transform receives geometric validation; hardware fused mode has an explicit calibration gate.

| Lines | Block |
|---:|---|
| 1–12 | module imports, constants, and module-level setup |
| 13–23 | class `AppConfig` |
| 26–40 | class `RadarConfig` |
| 43–60 | class `VisionConfig` |
| 63–66 | class `SyncConfig` |
| 69–97 | class `FusionConfig` |
| 102–108 | class `CalibrationMonitorConfig` |
| 111–117 | class `TrackerConfig` |
| 120–126 | class `MapConfig` |
| 129–136 | class `ApiConfig` |
| 139–143 | class `ResearchConfig` |
| 146–156 | class `ScannerConfig` |
| 159–166 | function `load_config` |

## `src/hybrid_scanner/radar/ti_iwr6843.py` — 335 lines

Highest-risk parser audited defensively: magic/header/packet/TLV bounds, signed side info, coordinate limits, UART resync, profile error handling.

| Lines | Block |
|---:|---|
| 1–24 | module imports, constants, and module-level setup |
| 25–185 | class `TiPacketParser` |
| 188–335 | class `TiIwr6843` |

## `src/hybrid_scanner/vision/realsense.py` — 139 lines

Hardware access is lazy, time-bounded, range-filtered, and reconnectable; no raw RGB persistence in the product path.

| Lines | Block |
|---:|---|
| 1–10 | module imports, constants, and module-level setup |
| 11–139 | class `RealSenseD435i` |

## `src/hybrid_scanner/sync.py` — 56 lines

Bounded latest-first queues prevent latency growth; duplicate radar frames are not replayed; nearest vision frame obeys skew limit.

| Lines | Block |
|---:|---|
| 1–8 | module imports, constants, and module-level setup |
| 9–56 | class `FrameBus` |

## `src/hybrid_scanner/fusion.py` — 128 lines

Fusion produces covariance and confidence from SNR, geometry, and live sensor trust; no unsupported object-identity claim is made.

| Lines | Block |
|---:|---|
| 1–10 | module imports, constants, and module-level setup |
| 11–128 | class `FusionEngine` |

## `src/hybrid_scanner/tracking.py` — 141 lines

Global association plus Kalman state prediction/update audited for target persistence, gating, confirmation, and deletion.

| Lines | Block |
|---:|---|
| 1–11 | module imports, constants, and module-level setup |
| 12–20 | class `_Track` |
| 23–141 | class `MultiTargetTracker` |

## `src/hybrid_scanner/calibration_monitor.py` — 51 lines

Rolling robust residual statistics flag likely calibration/mount drift without silently changing the transform.

| Lines | Block |
|---:|---|
| 1–9 | module imports, constants, and module-level setup |
| 10–51 | class `CalibrationDriftMonitor` |

## `src/hybrid_scanner/mapping.py` — 88 lines

Sparse map is bounded, decays, and prunes to avoid unbounded memory growth.

| Lines | Block |
|---:|---|
| 1–10 | module imports, constants, and module-level setup |
| 11–13 | class `_Voxel` |
| 16–88 | class `SparseOccupancyMap` |

## `src/hybrid_scanner/guidance.py` — 65 lines

Next-best-view logic is advisory only and never drives actuators.

| Lines | Block |
|---:|---|
| 1–8 | module imports, constants, and module-level setup |
| 9–65 | class `ActiveScanAdvisor` |

## `src/hybrid_scanner/health.py` — 70 lines

Freshness and error history become sensor trust; stale sensors cannot remain ready indefinitely.

| Lines | Block |
|---:|---|
| 1–9 | module imports, constants, and module-level setup |
| 10–15 | class `_SensorHealth` |
| 18–70 | class `HealthMonitor` |

## `src/hybrid_scanner/recording.py` — 39 lines

Disk I/O is moved off the real-time loop and queue overflow is bounded/accounted.

| Lines | Block |
|---:|---|
| 1–8 | module imports, constants, and module-level setup |
| 9–39 | class `JsonlRecorder` |

## `src/hybrid_scanner/workers.py` — 71 lines

Sensor faults reconnect with exponential backoff; stop/cleanup paths are explicit.

| Lines | Block |
|---:|---|
| 1–10 | module imports, constants, and module-level setup |
| 11–71 | class `ReconnectingWorker` |

## `src/hybrid_scanner/state.py` — 37 lines

Cross-thread snapshots deep-copy mutable state.

| Lines | Block |
|---:|---|
| 1–8 | module imports, constants, and module-level setup |
| 9–37 | class `StatusStore` |

## `src/hybrid_scanner/api.py` — 119 lines

Remote exposure requires auth; health/readiness/metrics/status boundaries reviewed; WebSocket disconnect is handled.

| Lines | Block |
|---:|---|
| 1–26 | module imports, constants, and module-level setup |
| 27–33 | function `_is_loopback` |
| 36–119 | function `build_app` |

## `src/hybrid_scanner/simulation.py` — 57 lines

Deterministic seeded multi-target simulation exercises fusion/tracking without hardware.

| Lines | Block |
|---:|---|
| 1–10 | module imports, constants, and module-level setup |
| 11–57 | class `Simulator` |

## `src/hybrid_scanner/engine.py` — 322 lines

Main orchestration audited for startup gates, bounded timing, worker lifecycle, signal shutdown, recording, health, calibration, tracking and guidance.

| Lines | Block |
|---:|---|
| 1–26 | module imports, constants, and module-level setup |
| 27–322 | class `ScannerEngine` |

## `src/hybrid_scanner/cli.py` — 87 lines

Operational commands expose doctor/run/version; doctor surfaces device permissions and calibration readiness.

| Lines | Block |
|---:|---|
| 1–18 | module imports, constants, and module-level setup |
| 19–54 | function `doctor` |
| 58–78 | function `run` |
| 82–83 | function `version` |

## `scripts/calibrate_from_csv.py` — 86 lines

Calibration uses Kabsch/SVD, rejects degenerate geometry, applies RMSE/P95 gates, and writes config atomically.

| Lines | Block |
|---:|---|
| 1–11 | module imports, constants, and module-level setup |
| 12–42 | function `rigid_transform` |
| 45–50 | function `atomic_yaml_write` |
| 53–82 | function `main` |

## `scripts/generate_release_manifest.py` — 60 lines

Release provenance hashes code/config artifacts and records calibration state without hashing transient logs/recordings.

| Lines | Block |
|---:|---|
| 1–12 | module imports, constants, and module-level setup |
| 13–18 | function `sha256` |
| 21–56 | function `main` |

## Verification performed

- Python bytecode compilation of `src/`, `tests/`, and `scripts/`.
- 11 automated tests covering parser variants, signed radar side-info, transform validation, timestamp skew, duplicate-frame prevention, fusion, tracking, calibration drift, and mapping/guidance.
- CLI package install/doctor smoke test using local build tooling.
- End-to-end simulation smoke test with JSONL recording.
- API smoke test on an alternate local port for `/health`, `/ready`, and `/version`.
- AST-based unused-import scan completed cleanly.
- Static-linter configuration is included in CI. The build environment could not download Ruff because outbound package installation is disabled, so Ruff itself was not executed locally; GitHub CI will execute it after push.
