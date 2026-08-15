# Deployment

## Recommended path

For hardware bring-up, deploy directly on the Linux host rather than putting USB/serial devices inside a container.

1. Install OS and updates.
2. Install Git + Python.
3. Install vendor SDK/runtime dependencies.
4. Clone repository.
5. Create virtual environment.
6. Run `hybrid-scanner doctor`.
7. Validate radar-only.
8. Validate vision-only.
9. Calibrate.
10. Validate fused mode.
11. Create a dedicated non-login `scanner` user.
12. Grant only required serial/device access.
13. Install the systemd unit.
14. Keep the API on loopback unless you intentionally place it behind an authenticated reverse proxy.

## Jetson

Use the current NVIDIA-supported JetPack/Jetson Linux path for your exact Orin Nano kit. Prefer NVMe storage for logs, datasets, builds, and future models.

## Logs/data

Default event recording is JSONL. Raw RGB recording is intentionally not implemented by default. If you add raw frames:
- document retention
- encrypt sensitive data at rest
- limit access
- define deletion policy
