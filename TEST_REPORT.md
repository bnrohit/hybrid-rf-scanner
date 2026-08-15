# Hybrid RF Scanner 2.0 — Build/Test Report

Date: 2026-08-15

## Automated tests

Final local test suite: **11 passed**.

Covered behaviors:
- TI TLV length mode: header-inclusive
- TI TLV length mode: payload-only
- signed TI SNR/noise side information
- configuration and rigid transform validation
- radar/vision timestamp skew gating
- duplicate radar-frame prevention
- uncertainty-aware fusion
- persistent multi-target tracking and confirmation
- calibration drift alerting
- sparse scene mapping
- active scan guidance

## Smoke tests completed

- Python bytecode compilation for `src/`, `tests/`, and `scripts/`
- editable package installation using locally available build tooling
- `hybrid-scanner version`
- `hybrid-scanner doctor`
- end-to-end deterministic simulation
- bounded JSONL event recording
- local API `/health`
- local API `/ready`
- local API `/version`
- AST-based unused import scan

## Environment limitations

Real TI IWR6843 and RealSense D435i hardware were not attached to this build environment, so hardware behavior is not claimed as validated. The final package intentionally blocks fused hardware startup while `calibration_validated: false`.

Ruff is configured in GitHub CI, but this build environment could not download the Ruff package because outbound package installation is disabled. The code still passed compilation, tests and the local AST unused-import check. After push, GitHub CI is configured to run Ruff, pytest with coverage, and `pip-audit`.

## Release decision

**Software foundation: ready for hardware acceptance testing.**

**Field-production release: blocked until the hardware acceptance and production checklists are completed on the exact final assembly.**
