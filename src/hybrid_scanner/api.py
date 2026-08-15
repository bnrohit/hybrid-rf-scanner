from __future__ import annotations

import asyncio
import hmac
import ipaddress
from importlib.metadata import version as package_version

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from prometheus_client import Counter, Gauge, Histogram, CONTENT_TYPE_LATEST, generate_latest

from hybrid_scanner.state import StatusStore


FRAMES = Counter("hybrid_scanner_frames_total", "Radar frames processed")
MEASUREMENTS = Gauge("hybrid_scanner_measurements", "Current fused measurements")
TRACKS = Gauge("hybrid_scanner_tracks", "Current tracks")
SYNC_SKEW = Gauge("hybrid_scanner_sync_skew_ms", "Matched radar/vision timestamp skew in ms")
LOOP_LATENCY = Histogram(
    "hybrid_scanner_loop_seconds",
    "Main processing loop duration",
    buckets=(0.0025, 0.005, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 1.0),
)
SENSOR_ERRORS = Counter("hybrid_scanner_sensor_errors_total", "Sensor errors", ["sensor"])


def _is_loopback(host: str) -> bool:
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def build_app(store: StatusStore, *, token: str | None, host: str, allow_loopback_without_token: bool) -> FastAPI:
    if not token and not (_is_loopback(host) and allow_loopback_without_token):
        raise RuntimeError(
            "API is bound beyond loopback without an auth token. Set HYBRID_SCANNER_API_TOKEN "
            "or bind the API to 127.0.0.1."
        )

    async def auth(authorization: str | None = Header(default=None)) -> None:
        if not token:
            return
        expected = f"Bearer {token}"
        if authorization is None or not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="invalid bearer token")

    app = FastAPI(title="Hybrid RF Scanner", version="2.0.0")

    @app.get("/health")
    async def health():
        snap = store.snapshot()
        return {
            "ok": bool(snap.get("healthy")),
            "ready": bool(snap.get("ready")),
            "last_error": snap.get("last_error"),
            "calibration": snap.get("calibration", {}),
            "sensors": snap.get("sensors", {}),
        }

    @app.get("/ready")
    async def ready():
        snap = store.snapshot()
        if not snap.get("ready"):
            raise HTTPException(status_code=503, detail="scanner not ready")
        return {"ready": True}

    @app.get("/status", dependencies=[Depends(auth)])
    async def status():
        return store.snapshot()

    @app.get("/tracks", dependencies=[Depends(auth)])
    async def tracks():
        return {"tracks": store.snapshot().get("tracks", [])}

    @app.get("/guidance", dependencies=[Depends(auth)])
    async def guidance():
        return {"guidance": store.snapshot().get("guidance")}

    @app.get("/version")
    async def version():
        try:
            installed = package_version("hybrid-rf-scanner")
        except Exception:
            installed = "2.0.0"
        return {"version": installed}

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.websocket("/ws")
    async def websocket_status(ws: WebSocket):
        if token:
            supplied = ws.headers.get("authorization") or ""
            if not hmac.compare_digest(supplied, f"Bearer {token}"):
                await ws.close(code=4401)
                return
        await ws.accept()
        try:
            while True:
                await ws.send_json(store.snapshot())
                await asyncio.sleep(0.20)
        except WebSocketDisconnect:
            pass

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        return HTMLResponse("""
<!doctype html><html><head><meta charset='utf-8'><title>Hybrid RF Scanner</title>
<style>body{font-family:system-ui;margin:2rem;max-width:1000px}pre{background:#111;color:#eee;padding:1rem;overflow:auto}.ok{font-weight:700}</style></head>
<body><h1>Hybrid RF Scanner 2.0</h1><p id='state'>Loading health…</p>
<p>Detailed status is protected when API authentication is enabled.</p><pre id='health'></pre>
<script>async function tick(){try{let r=await fetch('/health');let j=await r.json();document.getElementById('state').textContent=j.ok?'HEALTHY':'NOT READY';document.getElementById('health').textContent=JSON.stringify(j,null,2)}catch(e){document.getElementById('state').textContent=e}}setInterval(tick,1000);tick()</script></body></html>
""")

    return app
