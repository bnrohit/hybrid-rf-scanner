# Production Readiness Checklist

## Hardware baseline
- [ ] Exact IWR6843 board revision recorded
- [ ] TI firmware/demo image checksum recorded
- [ ] Radar CLI profile version-controlled and validated
- [ ] RealSense serial and firmware recorded
- [ ] Final rigid mount locked and tamper-marked
- [ ] USB power/brownout test completed
- [ ] Thermal soak completed at worst-case ambient
- [ ] NVMe endurance sized for configured logging

## Timing and calibration
- [ ] `fusion.calibration_validated=true` was produced by a passing calibration run
- [ ] Radar↔camera transform RMSE passes gate
- [ ] Calibration P95 error passes gate
- [ ] Independent ground-truth location test completed
- [ ] Radar/vision host timestamp skew measured p50/p95/p99
- [ ] Maximum accepted skew configured from data, not guesswork

## Reliability
- [ ] 24-hour soak test completed
- [ ] Radar unplug/replug recovery passed
- [ ] Camera unplug/replug recovery passed
- [ ] Corrupt UART packet recovery passed
- [ ] Disk-full behavior tested
- [ ] Service restart after process crash tested
- [ ] Memory growth checked over soak run

## Detection/tracking validation
- [ ] Ground-truth target dataset created
- [ ] Precision/recall reported by range and scene type
- [ ] Track-ID switches measured
- [ ] False positives per hour measured
- [ ] Occlusion performance measured
- [ ] Confidence calibration curve measured

## Security/privacy
- [ ] API is loopback-only or protected by a strong bearer token/reverse proxy
- [ ] Secrets are outside Git
- [ ] Service runs non-root
- [ ] Raw RGB storage remains disabled unless justified
- [ ] Data-retention/deletion policy approved
- [ ] `pip-audit` and dependency updates are green
- [ ] Threat model reviewed

## Release
- [ ] CI green on supported Python versions
- [ ] Version/tag created
- [ ] SBOM generated for release image
- [ ] Configuration and calibration checksum attached to release record
- [ ] Rollback package tested
