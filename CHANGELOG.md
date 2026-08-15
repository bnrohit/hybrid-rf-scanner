# Changelog

## 2.0.0 — 2026-08-15

- Rebuilt the runtime around bounded reconnecting sensor workers.
- Added timestamp matching and sensor trust.
- Replaced heuristic-only fusion with covariance-bearing probabilistic fusion.
- Added multi-target Kalman/Hungarian tracking.
- Added decaying sparse scene memory and active scan guidance.
- Added continuous calibration drift monitoring.
- Added a hard fused-hardware startup gate until calibration passes.
- Hardened TI UART parsing, including signed side-info and TLV length variants.
- Added non-blocking event recording, API authentication guard, metrics, systemd hardening, Docker simulation, Dependabot, dependency audit CI, and expanded tests.

## 1.0.0

- Initial production starter.
