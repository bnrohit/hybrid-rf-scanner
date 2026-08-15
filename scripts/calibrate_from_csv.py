from __future__ import annotations

import argparse
import csv
from pathlib import Path
import tempfile

import numpy as np
import yaml


def rigid_transform(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, float, float]:
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 3:
        raise ValueError("point arrays must both be Nx3")
    if len(a) < 3:
        raise ValueError("at least 3 correspondences are required")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("calibration points must be finite")

    a_center = a.mean(axis=0)
    b_center = b.mean(axis=0)
    aa = a - a_center
    bb = b - b_center
    if np.linalg.matrix_rank(aa) < 2:
        raise ValueError("calibration geometry is degenerate; spread points in 3D")

    h = aa.T @ bb
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1, :] *= -1
        r = vt.T @ u.T
    t = b_center - r @ a_center

    transform = np.eye(4)
    transform[:3, :3] = r
    transform[:3, 3] = t
    projected = (r @ a.T).T + t
    errors = np.linalg.norm(projected - b, axis=1)
    rmse = float(np.sqrt(np.mean(errors**2)))
    p95 = float(np.percentile(errors, 95))
    return transform, rmse, p95


def atomic_yaml_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False)
        temp_path = Path(fh.name)
    temp_path.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", default="config/scanner_config.yaml")
    parser.add_argument("--max-rmse", type=float, default=0.08)
    parser.add_argument("--max-p95", type=float, default=0.12)
    args = parser.parse_args()

    radar, camera = [], []
    with open(args.input, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            radar.append([float(row["radar_x"]), float(row["radar_y"]), float(row["radar_z"])])
            camera.append([float(row["camera_x"]), float(row["camera_y"]), float(row["camera_z"])])

    if len(radar) < 8:
        raise SystemExit("Use at least 8 well-spread correspondences for production calibration.")
    transform, rmse, p95 = rigid_transform(np.asarray(radar), np.asarray(camera))
    print(transform)
    print(f"RMSE={rmse:.4f} m; P95={p95:.4f} m")
    if rmse > args.max_rmse or p95 > args.max_p95:
        raise SystemExit("Calibration rejected by RMSE/P95 quality gates.")

    path = Path(args.config)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["fusion"]["radar_to_camera"] = transform.tolist()
    cfg["fusion"]["calibration_validated"] = True
    cfg["fusion"]["calibration_rmse_m"] = rmse
    cfg["fusion"]["calibration_p95_m"] = p95
    atomic_yaml_write(path, cfg)
    print(f"Updated {path}")


if __name__ == "__main__":
    main()
