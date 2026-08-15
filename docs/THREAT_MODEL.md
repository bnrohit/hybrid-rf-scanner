# Threat Model

## Assets
Sensor configuration, calibration transform, recorded target events, API status, device identity and future learned-model artifacts.

## Main threats
- Network exposure of unauthenticated status/control interfaces
- Malicious or accidental configuration changes
- USB/UART device spoofing or corrupt serial input
- Resource exhaustion from malformed packets or log growth
- Dependency compromise
- Privacy leakage if future builds retain RGB imagery

## Current controls
- API defaults to loopback and refuses a remote bind without a bearer token.
- Serial parser has hard packet, count and coordinate limits.
- Sensor input buffers and recording queues are bounded.
- Service runs non-root with systemd hardening.
- No secrets belong in the repository.
- CI includes dependency vulnerability audit.
- The default recorder stores target metadata rather than RGB frames.

## Not yet implemented
TLS termination, signed configuration bundles, secure boot/attestation, hardware device identity, remote fleet management and signed model artifacts.
