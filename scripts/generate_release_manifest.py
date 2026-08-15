from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import yaml


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default="config/scanner_config.yaml")
    parser.add_argument("--output", default="release-manifest.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    excludes = {".git", ".venv", ".pytest_cache", "__pycache__", "logs", "recordings"}
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in excludes for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel == args.output:
            continue
        files.append({"path": rel, "sha256": sha256(path), "bytes": path.stat().st_size})

    cfg_path = root / args.config
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    manifest = {
        "schema": "hybrid-rf-scanner.release-manifest.v1",
        "python": sys.version,
        "platform": platform.platform(),
        "configuration": {
            "node_id": cfg["app"]["node_id"],
            "calibration_validated": cfg["fusion"].get("calibration_validated", False),
            "calibration_rmse_m": cfg["fusion"].get("calibration_rmse_m"),
            "calibration_p95_m": cfg["fusion"].get("calibration_p95_m"),
            "config_sha256": sha256(cfg_path),
        },
        "files": files,
    }
    out = root / args.output
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
