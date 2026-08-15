# Hardware Acceptance Procedure

Do this on the **exact final scanner assembly**.

## 1. Record the baseline

Record:
- Jetson model and JetPack/Jetson Linux version
- TI board revision
- TI flashed binary/hash and mmWave SDK/demo version
- radar CLI profile hash
- RealSense serial, firmware and librealsense version
- mount revision
- power supply and USB hub/cable revision

## 2. Serial stability

```bash
ls -l /dev/serial/by-id/
udevadm info /dev/ttyACM0
udevadm info /dev/ttyACM1
```

Prefer `/dev/serial/by-id/...` paths in production config instead of enumeration-dependent names when the platform exposes stable IDs.

## 3. Camera stability

```bash
rs-enumerate-devices
```

Run the camera at the exact final stream configuration for at least one hour before fusion testing.

## 4. Separate sensor tests

```bash
hybrid-scanner run --mode radar-only
hybrid-scanner run --mode vision-only
```

Fix disconnects, brownouts and permission problems before calibration.

## 5. Calibration

Collect 8+ correspondences spread through the full operating volume and run:

```bash
python scripts/calibrate_from_csv.py --input calibration_points.csv --config config/scanner_config.yaml
```

Do not manually set `calibration_validated: true`.

## 6. Fused soak

```bash
hybrid-scanner run --mode fused --api
```

Run at least 24 hours while recording:
- loop p50/p95/p99 latency
- sync skew p50/p95/p99
- radar/camera disconnect count
- process RSS over time
- recorder drops
- calibration residual median/P95
- track ID switches
- false positives per hour

## 7. Fault injection

While running:
- unplug/replug radar
- unplug/replug camera
- restart the service
- temporarily remove network connectivity
- fill the log filesystem in a disposable test environment
- feed malformed/corrupt UART test packets in a lab harness

The process must recover or fail visibly; it must never silently report healthy while required sensors are stale.

## 8. Release record

```bash
python scripts/generate_release_manifest.py
sha256sum release-manifest.json
```

Attach the manifest, calibration CSV, validation report, firmware hashes and package/tag to the release record.
