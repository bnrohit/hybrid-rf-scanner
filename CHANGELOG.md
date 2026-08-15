# Changelog

## 2.0.1 — 2026-08-15

- Added `httpx2` to dev/test dependencies for Starlette 1.x `TestClient` compatibility on clean CI runners.
- Upgraded GitHub Actions checkout/setup-python steps to Node-24-based major versions.
- Fixed container API reachability while preserving token protection.
- Added explicit container/service API host/port environment overrides.
- Made fusion confidence fully radar-trust-gated and added multi-neighbor depth corroboration.
- Added synchronized-pair freshness to fused readiness.
- Respected `tracker.enabled` at runtime.
- Switched tracker covariance update to Joseph stabilized form.
- Made recorder shutdown and serialization failure reporting robust.
- Added timestamp-based radar delivery so radar frame-number resets do not stall processing.
- Made validated calibration require recorded RMSE/P95 quality metrics.
- Hardened API health information exposure and protected metrics when authentication is enabled.
- Expanded CI with compile, package build and dependency consistency checks.
- Expanded regression suite from 11 to 20 tests for this release.

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
