# Calibration

Rigid radar/camera mounting is mandatory for useful fusion.

## Target
Use a target that both sensing systems can localize consistently. Collect points throughout the intended working volume rather than clustering them in one small area.

## Procedure
1. Lock the radar and D435i into the final bracket.
2. Do not move either sensor relative to the other.
3. Collect at least 8 paired 3D correspondences.
4. Spread samples in x, y, z.
5. Save them as `calibration_points.csv`.
6. Run `scripts/calibrate_from_csv.py`.
7. Record RMSE.
8. Reject calibration if error exceeds your validated threshold.
9. Re-test calibration after any impact, bracket change, or sensor replacement.

## Production note
Calibration RMSE alone is not enough. Validate fused target location against independent ground truth over the full operational volume.
