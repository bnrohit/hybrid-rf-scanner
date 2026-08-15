# Hybrid RF Scanner 2.0.1 — Build/Test Report

Date: 2026-08-15

## Automated tests

Final local regression suite: **20 passed**.

Covered behaviors include:
- TI TLV header-inclusive and payload-only length modes
- signed TI SNR/noise side information
- configuration and rigid-transform validation
- mandatory validated-calibration RMSE/P95 metrics
- calibration monitor validation
- radar/vision timestamp-skew gating
- timestamp-based radar delivery across firmware frame-number resets
- zero-trust radar suppression
- uncorroborated-target confidence penalty
- uncertainty-aware radar/depth fusion
- persistent multi-target tracking and confirmation
- calibration drift alerting
- sparse scene mapping and active scan guidance
- bounded recorder shutdown/error state
- minimal public health response
- protected metrics for remote API mode
- remote API binding rejected without a token
- API host environment override

## GitHub clean-runner findings corrected

- Starlette 1.x `TestClient` required `httpx2`; the dev extra now installs it explicitly.
- GitHub Actions checkout/setup-python were upgraded to v6.
- `pip-audit` flagged runner `setuptools 79.0.1` as PYSEC-2026-3447; build/dev tooling and CI now require `setuptools>=83`.
- Project license metadata was moved to the current SPDX string form.

## Release decision

**Software release 2.0.1: GitHub CI is green across Python 3.10, 3.11, and 3.12; suitable for hardware acceptance testing.**

**Field-production deployment remains blocked until hardware acceptance passes on the exact TI firmware, D435i, mount, cables, power system and compute platform.**
