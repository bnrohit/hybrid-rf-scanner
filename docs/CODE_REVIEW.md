# Production Code Review — v2.0.1

## Review scope

The complete production Python tree, deployment files, package metadata, Docker configuration, systemd unit, test suite, and GitHub Actions workflow were reviewed after the first GitHub publication attempt.

## High-impact defects corrected

1. **Docker reachability:** the published port targeted container port 8080 while Uvicorn bound only to container loopback. Container deployment now overrides the in-container API host to `0.0.0.0` and requires a token, while Docker still publishes only to host loopback.
2. **Fusion trust bypass:** SNR/geometry could dominate confidence even when radar health trust was near zero. Confidence is now gated by radar trust, so an unhealthy primary sensor cannot emit a high-confidence target.
3. **Synchronization readiness:** fresh radar and camera streams were sufficient for readiness even when no pair met the timestamp skew gate. Fused readiness now also requires a recent successfully synchronized pair.
4. **Tracker disable ignored:** `tracker.enabled` existed in configuration but runtime always executed tracking. Runtime now honors the setting.
5. **Kalman covariance stability:** tracker covariance used the simplified update. It now uses the Joseph stabilized update and re-symmetrizes covariance.
6. **Radar restart/frame reset:** radar delivery depended on frame number equality. Runtime consumption now uses monotonic receive timestamps, so firmware frame-number resets after reconnect do not stall the pipeline.
7. **Recorder shutdown/error visibility:** a full queue or JSON serialization failure could terminate/strand recording without good state reporting. Recorder now reports written/dropped/error/queue state and has bounded shutdown behavior.
8. **Startup resource lifetime:** API/hardware startup happened outside the main cleanup region. Startup and runtime now share one `try/finally`, and the Uvicorn server is explicitly asked to exit.
9. **Calibration assertion weakness:** `calibration_validated: true` could be set without quality metrics. Validation now requires both RMSE and P95 metadata.
10. **API information exposure:** public health returned detailed sensor/calibration/error data and metrics stayed open even with a token. Public health is now minimal; metrics use the same bearer-token guard.
11. **Nested config defaults:** nested Pydantic model defaults now use `default_factory`.
12. **CI gaps:** CI now compiles Python, runs Ruff, tests with coverage, checks installed dependency consistency, builds wheel/sdist, and runs `pip-audit`.

## Remaining hardware-validation gates

Software tests cannot prove radar UART compatibility with every TI firmware image, RealSense USB/firmware stability, actual radar↔camera timing offset, thermal behavior, EMI sensitivity, calibration durability, or target performance. Those remain explicit hardware acceptance gates rather than being hidden behind a “production ready” label.
