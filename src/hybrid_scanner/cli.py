from __future__ import annotations

import os
import platform
from pathlib import Path
import sys

from loguru import logger
import typer

from hybrid_scanner import __version__
from hybrid_scanner.config import load_config
from hybrid_scanner.engine import ScannerEngine

app = typer.Typer(no_args_is_help=True, help="Hybrid RF Scanner control CLI")


@app.command()
def doctor(
    config: str = typer.Option("config/scanner_config.yaml", "--config", "-c"),
    hardware: bool = typer.Option(False, "--hardware", help="Fail if required hardware is unavailable"),
) -> None:
    """Validate config, runtime, device paths, permissions, and optional SDKs."""
    cfg = load_config(config)
    failures: list[str] = []
    typer.echo(f"Hybrid RF Scanner: {__version__}")
    typer.echo(f"Python: {sys.version.split()[0]}")
    typer.echo(f"OS: {platform.platform()}")
    typer.echo(f"Config: OK ({config})")

    for label, path in [("Radar CLI", cfg.radar.config_port), ("Radar DATA", cfg.radar.data_port)]:
        p = Path(path)
        exists = p.exists()
        rw = os.access(p, os.R_OK | os.W_OK) if exists else False
        typer.echo(f"{label}: {'FOUND' if exists else 'NOT FOUND'}; rw={rw}; {path}")
        if hardware and (not exists or not rw):
            failures.append(f"{label} is unavailable or lacks read/write permission")

    profile = Path(cfg.radar.profile_path)
    typer.echo(f"Radar profile: {'FOUND' if profile.exists() else 'NOT FOUND'} ({profile})")
    if hardware and not profile.exists():
        failures.append("radar profile is missing")
    typer.echo(
        "Fusion calibration: "
        + (
            f"VALIDATED (RMSE={cfg.fusion.calibration_rmse_m}, P95={cfg.fusion.calibration_p95_m})"
            if cfg.fusion.calibration_validated
            else "NOT VALIDATED — fused hardware mode will be blocked"
        )
    )

    try:
        import pyrealsense2 as rs
        ctx = rs.context()
        devices = list(ctx.query_devices())
        typer.echo(f"pyrealsense2: installed; devices={len(devices)}")
        if hardware and cfg.vision.enabled and not devices:
            failures.append("no RealSense device detected")
    except Exception as exc:
        typer.echo(f"pyrealsense2: unavailable or no usable runtime ({exc})")
        if hardware and cfg.vision.enabled:
            failures.append("RealSense runtime/device unavailable")

    if cfg.api.host not in {"127.0.0.1", "localhost", "::1"} and not cfg.api.token():
        typer.echo("SECURITY: remote API bind requires HYBRID_SCANNER_API_TOKEN")
    if hardware and not cfg.fusion.calibration_validated:
        failures.append("fusion calibration is not validated")
    typer.echo("Simulation mode: READY")
    if failures:
        for failure in failures:
            typer.echo(f"FAIL: {failure}", err=True)
        raise typer.Exit(code=1)


@app.command()
def run(
    config: str = typer.Option("config/scanner_config.yaml", "--config", "-c"),
    mode: str = typer.Option("fused", help="fused | radar-only | vision-only"),
    simulation: bool = typer.Option(False, "--simulation"),
    api: bool = typer.Option(False, "--api"),
) -> None:
    """Run real-time sensing pipeline."""
    if mode not in {"fused", "radar-only", "vision-only"}:
        raise typer.BadParameter("mode must be fused, radar-only, or vision-only")
    cfg = load_config(config)
    logger.remove()
    logger.add(sys.stderr, level=cfg.app.log_level)
    Path(cfg.app.log_file).parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        cfg.app.log_file,
        level=cfg.app.log_level,
        rotation=cfg.app.log_rotation,
        retention="14 days",
        enqueue=True,
    )
    ScannerEngine(cfg, mode=mode, simulation=simulation, api_enabled=api).run_forever()


@app.command()
def version() -> None:
    typer.echo(__version__)


if __name__ == "__main__":
    app()
