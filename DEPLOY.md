# Deploying OBSCURA

OBSCURA runs the synthetic feed by default, so it deploys anywhere without a
camera. The container builds the React frontend and serves it from FastAPI on a
single port — one container, one URL.

## Option 1 — Docker (local or any host), one command
```bash
docker compose up --build
```
Open http://localhost:8000 . That's the whole app (dashboard + API) on one port.

## Option 2 — Run the image directly
```bash
docker build -t obscura .
docker run -p 8000:8000 obscura
```

## Option 3 — Render / Railway / Fly.io (free tiers)
These platforms build the Dockerfile for you:
1. Push this repo to GitHub (done).
2. On Render: New → Web Service → connect the repo → it auto-detects the Dockerfile.
3. No build/start command needed (the Dockerfile's CMD handles it).
4. The platform sets `$PORT`; the app already binds to it.
5. Deploy → you get a public https URL serving the live dashboard.

## Notes
- The container uses `requirements-core.txt` (no MediaPipe) for a lean, reliable
  image. The synthetic feed + all guarantees work fully.
- For real video redaction on a server you'd add a video source and the model
  files; most deployments demo the simulation, which needs nothing extra.
- The on-screen "true count" is a demo-only honesty panel; remove the `/truth`
  route for a real production deployment.
