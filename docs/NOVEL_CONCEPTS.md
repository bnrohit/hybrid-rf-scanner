# Advanced Product Concepts

The word "novel" here means **product differentiation ideas**, not a claim that no prior research or product has ever explored them. Patent novelty requires a formal prior-art search.

## Implemented in v2

### 1. Trust-weighted probabilistic fusion
Every sensor has a live trust score based on freshness and error history. Radar/depth fusion turns that trust plus measurement uncertainty into covariance rather than only a hand-tuned confidence number.

### 2. Persistent multi-target identity
A constant-velocity Kalman tracker and global assignment maintain target IDs through noisy frames and short dropouts.

### 3. Active scan advisor
The system identifies the most uncertain confirmed track and recommends a human operator motion that increases parallax. It is advisory only; it does not control motion hardware.

### 4. Decaying RF/depth scene memory
A bounded sparse voxel evidence map lets the product remember persistent target regions while naturally forgetting stale evidence.

### 5. Privacy-first sensing mode
The production pipeline needs depth geometry, not stored RGB imagery. The default configuration records target metadata and counts rather than raw visual frames.

### 6. Firmware-variant-aware radar parser
TLV length semantics are explicit/auto-detected, packet sizes are bounded, malformed packets are isolated, and signed side-information is handled correctly.

### 7. Continuous calibration-drift sentinel
The system monitors the robust median and P95 radar↔depth residual over a rolling window. A loose mount, impact, or changed sensor geometry can therefore be surfaced before it silently poisons fusion.

### 8. Occlusion-aware evidence state
Each fused measurement records whether depth corroborates the radar return or whether it is radar-only / potentially occluded. This preserves a useful distinction instead of forcing every radar return into a visual-detection assumption.

## Research extensions intentionally NOT claimed as complete

### Coherent raw-ADC aperture imaging
Add DCA1000 raw ADC capture, phase-stable timestamping, motion compensation from an external high-grade IMU, and coherent back-projection. Point-cloud TLVs are not a substitute for raw coherent ADC data.

### Multi-static scanner mesh
Synchronize multiple radar nodes with hardware time distribution/PTP, estimate inter-node extrinsics, and fuse raw or intermediate radar observables. This requires a much stricter clock architecture than the current USB product.

### Learned micro-Doppler/material signatures
Build a labeled dataset, version the acquisition geometry, train a calibrated model, and report class uncertainty. Never infer "metal type" or a specific object identity from SNR alone.

### Neural scene completion
Use radar/depth evidence to estimate likely geometry behind visual occlusion. This should be a separate learned model with ground-truth evaluation, not mixed into the safety-critical measurement layer.

### Autonomous next-best-view robotics
The current advisor can become a planner only after collision sensing, robot kinematics, safety constraints, and formal fail-safe behavior are added.
