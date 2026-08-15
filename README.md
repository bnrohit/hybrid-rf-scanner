# Hybrid RF Scanner 2.0

Production-grade **foundation** for a real-time TI IWR6843 + RealSense D435i sensing product.

It is substantially stronger than v1: defensive radar parsing, independent reconnecting sensor workers, timestamp matching, trust-weighted probabilistic fusion, persistent multi-target tracking, decaying scene memory, active scan guidance, bounded async recording, API security, metrics, CI and hardware validation gates.

> Production-grade software does **not** mean hardware-validated product. You must complete `docs/PRODUCTION_CHECKLIST.md` on the exact radar firmware, camera, mount and compute platform before field deployment.

## Key product capabilities

- TI xWR68xx-style UART point-cloud ingestion
- RealSense D435i depth + IMU ingestion
- bounded real-time frame bus and nearest-timestamp synchronization
- live sensor trust from freshness/error history
- continuous calibration-drift sentinel (median/P95 residual)
- uncertainty-aware radar/depth fusion with occlusion/corroboration state
- Kalman + Hungarian multi-target tracking
- persistent decaying 3D voxel evidence map
- human-in-the-loop next-best-view guidance
- privacy-first event recording (no raw RGB by default)
- `/health`, `/ready`, `/status`, `/tracks`, `/guidance`, `/metrics`, WebSocket
- remote API exposure blocked unless a token is configured
- exponential-backoff sensor reconnect
- simulation mode and deterministic tests
- Docker simulation deployment and hardened systemd service

## Hardware

Recommended high-performance edge path:
- NVIDIA Jetson Orin Nano Super 8 GB or stronger Orin device
- TI IWR6843ISK-ODS
- Intel/RealSense D435i
- NVMe storage
- rigid calibrated mount
- powered USB 3 hub only if the host cannot provide stable peripheral power

For coherent raw-ADC aperture imaging, add a TI DCA1000-class raw data capture path and build a separate validated raw-signal pipeline. The normal point-cloud UART path is not raw coherent ADC capture.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Hardware camera support:

```bash
# First install a librealsense build compatible with your OS/JetPack.
pip install -r requirements-hardware.txt
```

Development:

```bash
pip install -e .[dev]
ruff check src tests scripts
pytest
```

## Simulation first

```bash
hybrid-scanner doctor
hybrid-scanner run --simulation --api
```

Then open `http://127.0.0.1:8080/`.

## Hardware bring-up order

1. Flash and document the exact TI firmware/demo.
2. Confirm stable serial device names with `ls -l /dev/serial/by-id/`.
3. Update `config/scanner_config.yaml`.
4. Verify RealSense with `rs-enumerate-devices`.
5. Run `hybrid-scanner doctor`.
6. Run `hybrid-scanner run --mode radar-only`.
7. Run `hybrid-scanner run --mode vision-only`.
8. Collect calibration correspondences and run `scripts/calibrate_from_csv.py`. The script marks calibration validated only after RMSE/P95 gates pass.
9. Run `hybrid-scanner run --mode fused --api`. Hardware fused mode refuses to start while `calibration_validated: false`.
10. Complete the production checklist.

## Calibration

CSV format:

```csv
radar_x,radar_y,radar_z,camera_x,camera_y,camera_z
0.10,1.00,0.00,0.12,0.98,0.03
```

Use at least 8 well-spread points:

```bash
python scripts/calibrate_from_csv.py --input calibration_points.csv --config config/scanner_config.yaml
```

The script rejects the transform if RMSE or P95 error exceeds configured command-line gates.

## Secure remote API

Loopback requires no token by default. If binding to a network interface:

```bash
export HYBRID_SCANNER_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Then set `api.host` to the required interface. Detailed endpoints expect:

```text
Authorization: Bearer <token>
```

Prefer an authenticated TLS reverse proxy for real remote deployments.

## Advanced concepts

See:
- `docs/NOVEL_CONCEPTS.md`
- `docs/ARCHITECTURE.md`
- `docs/CODE_REVIEW.md`
- `docs/THREAT_MODEL.md`
- `docs/PRODUCTION_CHECKLIST.md`

No claim is made that these concepts are globally unprecedented. A patent/novelty claim needs a formal prior-art search.
