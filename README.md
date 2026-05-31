<div align="center">

# OBSCURA

### See the threat. Not the person.

**Public-safety monitoring that is *mathematically incapable* of becoming mass surveillance.**

[Five Guarantees](#the-five-guarantees) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Tests](#tests) · [Deploy](#deploy)

Built for **Codorra 2026** — theme: *Mass Surveillance vs Public Safety* · Team **VORTEX**

</div>

---

## The problem

Modern public-safety systems — CCTV, crowd analytics, facial recognition — work by
collecting identity. That is exactly what erodes privacy. Cities want safety;
citizens fear surveillance; today you are forced to pick one.

**OBSCURA refuses to choose.** It delivers the safety signal authorities actually
need — crowd density, surges, anomalies — while making the identification of any
individual *structurally impossible*. And on the rare occasion lawful access is
required, no single party can unlock an identity, and every unlock is permanently
and publicly recorded.

## The five guarantees

| # | Guarantee | How |
|---|-----------|-----|
| 1 | **Anonymize at source** | Faces are detected and redacted (pixelate + blur) at the edge *before* any feature is computed or stored. Raw pixels never leave the anonymizer. |
| 2 | **Differential privacy** | Released statistics carry calibrated Laplace noise; each zone holds a privacy budget that regenerates over time and *refuses* to over-report; groups below *k* are suppressed (k-anonymity). |
| 3 | **Threshold cryptography** | Identities are AES-GCM sealed; the key is split via **Shamir 2-of-3** across police, an oversight officer, and the judiciary. No single party can de-anonymize anyone. |
| 4 | **Tamper-evident audit** | Every unlock is appended to a SHA-256 hash chain. Altering any past entry breaks the chain — anyone can verify the published head. |
| 5 | **Measured privacy** | A red-team **Privacy Auditor** continuously attacks our *own* redacted output, attempting re-identification. Its failure rate is published live as a Privacy Score. We don't claim privacy — we measure an attacker's inability to break it. |

Plus a **Safety Brain** (autoencoder anomaly detection on movement, never identity)
and a **DP-bound assistant** that can answer questions only from the
differentially-private aggregate layer — structurally unable to return a person.

## Architecture

```
                          Live video feed
                                │
                       Edge anonymization
            (detect + redact faces; derive count, density,
             motion, pose — raw pixels discarded)
                        ╱                ╲
            anonymous features        sealed identity crop
                   │                         │
        ┌──────────┴─────────┐      AES-GCM seal; key split via
        │                    │      Shamir 2-of-3, key discarded
   Differential          Safety Brain               │
     privacy          (autoencoder anomaly    Accountable break-glass
  (Laplace + budget     detection)             (t-of-n quorum unlock,
   + k-anonymity)           │                   every unlock audited)
        │                   │                         │
   Authority dashboard  Threat alerts        Tamper-evident public ledger

   Privacy Auditor (red-team): attacks the redacted output, fails,
   and publishes the failure rate as the live Privacy Score.
```

Full detail: [`docs/architecture.md`](docs/architecture.md).

## Quick start

Two terminals. The backend runs a synthetic feed by default, so the entire demo
works with **no camera and no heavy setup**.

**Backend**
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --port 8080
```

**Frontend** (second terminal)
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. (Dev proxy forwards `/api` → backend on 8080.)

### Real video (optional)
Download the res10 model files into `backend/models/` (see its README), then:
```bash
# PowerShell
$env:OBSCURA_VIDEO="C:\path\to\clip.mp4"   # or "0" for a live webcam
uvicorn app.main:app --port 8080
```
Click **Use real feed** in the dashboard. Detection threshold is tunable with
`OBSCURA_FACE_CONF` (default 0.35; lower catches smaller faces).

## Tests
```bash
cd backend
python -m pytest -q          # 12 tests, fully isolated
```
Covers the Laplace mechanism + budget regeneration, Shamir reconstruction, AES
sealing, tamper detection, and a full API smoke test.

## Deploy
One command, whole app on one port:
```bash
docker compose up --build    # then open http://localhost:8000
```
Or push to Render / Railway / Fly.io — they build the Dockerfile automatically.
See [`DEPLOY.md`](DEPLOY.md).

## Tech stack
**Backend:** Python · FastAPI · pure-Python differential privacy · Shamir secret
sharing over a 521-bit prime field · AES-GCM · SHA-256 hash chain · scikit-learn
autoencoder · OpenCV (res10 DNN + Haar) face redaction · ORB re-identification attacker.
**Frontend:** React · Vite · a forensic-console UI with a live raw-vs-redacted reveal.
**Quality:** 12 automated tests · Dockerized · one-command deploy.

## What's real vs. demo
All five guarantees are real and tested. The default feed is synthetic so it runs
anywhere; the real OpenCV camera/video path is implemented and enabled with a video
source. The on-screen "true count" is a demo-only honesty panel to make the privacy
gap visible — it would not exist in production.

## Repository layout
```
backend/
  app/
    anonymizer/   edge face redaction, pose, MJPEG, synthetic feed
    privacy/      differential privacy, re-ID auditor, DP-bound assistant
    safety/       autoencoder anomaly detection
    vault/        Shamir secret sharing, AES, hash-chain audit
    api/          FastAPI routes
  tests/          pytest suite
frontend/         React + Vite dashboard
docs/             architecture, demo script, submission writeup
Dockerfile · docker-compose.yml · DEPLOY.md
```

## Team VORTEX
Raktim Chandra · Nipun Dewangan · Juhi Hai · Pronov Mazumdar

## License
MIT — see [`LICENSE`](LICENSE).
