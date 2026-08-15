from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


EXCLUDED_DIRS = {
    ".git", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "__pycache__", "build", "dist", "logs", "recordings",
}
TRACKED_PREFIXES = (".github/", "config/", "firmware/", "scripts/", "src/")
TRACKED_ROOT_FILES = {
    ".dockerignore", ".env.example", ".gitignore", "Dockerfile", "Makefile",
    "docker-compose.yml", "pyproject.toml", "requirements.txt",
    "requirements-dev.txt", "requirements-hardware.txt",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def include_file(path: Path, root: Path, output: str) -> bool:
    if not path.is_file():
        return False
    rel = path.relative_to(root).as_posix()
    if rel == output:
        return False
    if any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in path.parts):
        return False
    return rel in TRACKED_ROOT_FILES or rel.startswith(TRACKED_PREFIXES)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default="config/scanner_config.yaml")
    parser.add_argument("--output", default="release-manifest.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    cfg_path = root / args.config
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    files = {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if include_file(path, root, args.output)
    }
    manifest = {
        "schema": "hybrid-rf-scanner.release-manifest.v2",
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
