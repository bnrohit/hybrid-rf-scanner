# Hybrid RF Scanner 2.0.1 — Build/Test Report

Date: 2026-08-15

## Automated tests

Final local regression suite: **20 passed**.

Covered behaviors include:
- TI TLV length mode: header-inclusive
- TI TLV length mode: payload-only
- signed TI SNR/noise side information
- configuration and rigid-transform validation
- validated-calibration metrics are mandatory
- calibration monitor window/sample validation
- radar/vision timestamp-skew gating
- timestamp-based radar delivery across firmware frame-number resets
- duplicate/stale radar-frame prevention
- zero-trust radar produces no fused measurement
- uncorroborated radar measurements are confidence-penalized
- uncertainty-aware radar/depth fusion
- persistent multi-target tracking and confirmation
- calibration drift alerting
- sparse scene mapping and active scan guidance
- recorder close/error state handling
- minimal public health response
- authenticated metrics endpoint for remote API mode
- remote API binding rejected without a token
- explicit API host environment override

## Smoke/build checks completed

- Python bytecode compilation for `src/`, `tests/`, and `scripts/`
- editable package installation with locally available build tooling
- `hybrid-scanner version`
- `hybrid-scanner doctor`
- end-to-end deterministic simulation
- clean engine shutdown
- bounded JSONL event recording
- local API `/health`, `/ready`, and `/version`
- YAML parsing for application config, Docker Compose, CI, and Dependabot files
- wheel build using `--no-build-isolation`
- AST-based unused-import scan

## Defects corrected in 2.0.1

- Docker port publishing could not reach an API bound to container loopback.
- Fused readiness could remain true during prolonged radar/camera pairing failure.
- `tracker.enabled` was not honored.
- Low radar trust could still yield overly strong fused confidence.
- Radar delivery used firmware frame numbers, which can reset after reconnect.
- Recorder errors/drop state were not operationally visible.
- API shutdown was not explicitly coordinated with engine shutdown.
- Startup failure could leave partially started resources behind.
- Calibration validation allowed an asserted boolean without quality metrics.
- Remote `/metrics` exposure did not share the detailed-endpoint authentication gate.

## Environment limitations

Real TI IWR6843 and RealSense D435i hardware are not attached to this execution environment, so hardware behavior is **not** claimed as validated. Hardware fused mode remains blocked while `calibration_validated: false`.

This execution environment does not have all project dependencies installed globally (notably `pyserial`) and outbound package installation is restricted. The project declares the missing runtime dependency correctly; GitHub CI installs the package dependencies in a clean runner before executing lint, tests, build, `pip check`, and `pip-audit`.

## Release decision

**Software release 2.0.1: suitable for GitHub CI and hardware acceptance testing.**

**Field-production deployment: blocked until the hardware acceptance and production checklists pass on the exact final radar firmware, camera, mount, cables, power system, and compute platform.**
