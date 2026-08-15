# v1 → v2 Code Review

This document records the engineering audit performed before the v2 rewrite.

## `config.py`
- v1 validated only matrix shape; v2 validates finiteness, homogeneous last row, approximate orthonormality and determinant.
- Added bounded configuration for parser safety, sensor reconnection, synchronization, tracking, mapping, API authentication and research flags.

## `radar/ti_iwr6843.py`
- Fixed TI side-info parsing from unsigned `uint16` to signed `int16`.
- Removed a single hard-coded TLV-length assumption and added configurable/automatic semantics.
- Added coordinate/packet/count safety limits.
- Added bounded stream buffer and resynchronization accounting.
- Added CLI error detection when loading a radar profile.
- Radar frames now carry host monotonic timestamps and parser warnings.

## `vision/realsense.py`
- Replaced tight polling with bounded wait/timeout behavior.
- Added depth-range filtering, deterministic downsampling, device metadata and host monotonic timestamps.
- Motion-frame extraction is defensive rather than assumed.
- Device disconnects propagate to the reconnect worker.

## `engine.py`
- Removed disk writes from the critical loop; recording is now queued.
- Added independent reconnecting sensor workers and a bounded latest-frame bus.
- Added timestamp matching instead of blindly fusing whichever frames arrived sequentially.
- Added live sensor trust, readiness/staleness, calibration-drift monitoring, tracker, scene memory and guidance.
- Added SIGTERM handling for systemd/container shutdown.

## `fusion.py`
- Replaced fixed 60/40 confidence with uncertainty-aware Gaussian measurement fusion.
- Confidence now incorporates SNR, geometric consistency and live sensor trust.
- Output includes covariance so downstream logic can reason about uncertainty.

## `api.py`
- Added readiness endpoint and authentication guard for non-loopback exposure.
- Protected detailed state while leaving basic health/metrics suitable for monitoring.
- Added loop latency, track, measurement and synchronization metrics.
- WebSocket disconnects are handled cleanly.

## `state.py`
- Snapshot now deep-copies state to avoid exposing mutable structures across threads.

## New modules
- `sync.py`: bounded timestamp matching.
- `tracking.py`: Kalman + Hungarian multi-target tracking.
- `health.py`: freshness/error-derived trust.
- `mapping.py`: bounded decaying sparse scene memory.
- `guidance.py`: advisory next-best-view logic.
- `recording.py`: bounded asynchronous JSONL recording.
- `workers.py`: exponential-backoff hardware reconnect.

## Remaining hardware-validation risks
- Exact TI firmware/profile compatibility must be tested on the actual flashed IWR6843 image.
- USB latency is not deterministic synchronization; measure skew and define acceptance thresholds.
- RealSense runtime compatibility depends on the Linux/JetPack/librealsense combination.
- Calibration must be validated over the actual operating volume.
- Classification claims require a real labeled dataset and independent test set.
