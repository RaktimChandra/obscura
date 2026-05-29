"""OBSCURA backend entrypoint.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import asyncio
import contextlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, SYNTHETIC_FEED_HZ
from . import store
from .api import routes
from .anonymizer.engine import SyntheticFeed
from .vault import vault


async def _feed_loop():
    """Push synthetic anonymous frames into the shared buffer and run the real
    Privacy Auditor: enroll each original synthetic face, then attempt to
    re-identify its blurred version. Redaction destroys the ORB structure, so
    the attacker fails — and that failure rate is measured, not assumed."""
    feed = SyntheticFeed("zone-A")
    while True:
        frame, faces = feed.next_frame()
        routes.feature_buffer.append(frame)
        for fid, orig_gray, red_gray in faces:
            routes.auditor.enroll(fid, orig_gray)
            routes.auditor.attempt_reid(red_gray, fid)
        await asyncio.sleep(1.0 / SYNTHETIC_FEED_HZ)


def create_app() -> FastAPI:
    app = FastAPI(title="OBSCURA", version="0.1.0",
                  description="Public safety that cannot become mass surveillance.")
    app.add_middleware(
        CORSMiddleware, allow_origins=CORS_ORIGINS,
        allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(routes.router)

    @app.on_event("startup")
    async def _startup():
        store.init_db()
        # Seed a couple of sealed demo identities for the break-glass demo.
        app.state.demo = {
            "alice": vault.seal_identity("Alice K. | cam-07 | 2026-05-30 21:14"),
            "bob": vault.seal_identity("Bob R. | cam-02 | 2026-05-30 21:15"),
        }
        app.state.feed_task = asyncio.create_task(_feed_loop())

    @app.on_event("shutdown")
    async def _shutdown():
        task = getattr(app.state, "feed_task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    @app.get("/healthz")
    def healthz():
        return {"name": "OBSCURA", "status": "ok",
                "tagline": "See the threat. Not the person."}

    @app.get("/video/{kind}")
    def video(kind: str):
        """Real CV path: stream raw or redacted MJPEG from a video file.
        Enable by setting OBSCURA_VIDEO=/path/to/clip.mp4 and placing the
        res10 model files in backend/models/. Returns 503 in synthetic mode so
        the frontend cleanly falls back to the built-in simulation."""
        import os
        from fastapi.responses import StreamingResponse
        src = os.environ.get("OBSCURA_VIDEO")
        if not src:
            raise HTTPException(503, "real video mode not configured")
        from .anonymizer.engine import RealAnonymizer, mjpeg_stream
        try:
            anon = RealAnonymizer("zone-A")
        except Exception as e:
            raise HTTPException(503, f"anonymizer unavailable: {e}")
        gen = mjpeg_stream(src, anon, redacted=(kind != "raw"),
                           auditor=routes.auditor)
        return StreamingResponse(
            gen, media_type="multipart/x-mixed-replace; boundary=frame")

    @app.get("/demo/records")
    def demo_records():
        """Convenience: the sealed demo identities and their holder shares,
        so the frontend can drive the break-glass demo."""
        return getattr(app.state, "demo", {})

    # Production: serve the built frontend from the same origin (one container).
    # Off by default so local dev (Vite on 5173) is untouched.
    import os as _os
    if _os.environ.get("OBSCURA_SERVE_FRONTEND") == "1":
        from fastapi.staticfiles import StaticFiles
        _static = _os.path.join(_os.path.dirname(__file__), "static")
        if _os.path.isdir(_static):
            app.mount("/", StaticFiles(directory=_static, html=True), name="spa")

    return app


app = create_app()
