# OBSCURA

**See the threat. Not the person.**

Public-safety surveillance that is *mathematically incapable* of becoming mass
surveillance. OBSCURA gives authorities the safety signal they need — crowd
density, surges, anomalies — while making individual identification structurally
impossible. When exceptional access is genuinely required, it takes a quorum of
independent parties to unlock a single identity, and every unlock is written to
a public, tamper-evident ledger.

Built for **Codorra 2026** — theme: *Mass Surveillance vs Public Safety*.
Team **VORTEX** — Raktim Chandra · Nipun Dewangan · Juhi Hai · Pronov Mazumdar.

---

## The five guarantees
1. **Anonymize at source** — faces/plates redacted at the edge before anything is stored.
2. **Differential privacy** — released counts carry Laplace noise; each zone has an ε budget we refuse to exceed; small groups are suppressed (k-anonymity).
3. **Threshold cryptography** — identities are AES-sealed; the key is split via Shamir 2-of-3 across police, an oversight officer, and the judiciary. No one party can un-blur anyone.
4. **Tamper-evident audit** — every unlock is appended to a SHA-256 hash chain anyone can verify; editing the past breaks the chain.
5. **Measured privacy** — a Privacy Auditor runs adversarial re-identification on our own redacted output and fails; that failure rate is the published Privacy Score.

Plus: an **autoencoder Safety Brain** (anomaly detection on movement, not identity)
and a **DP-bound NL assistant** that can only ever read privacy-protected aggregates.

---

## Quick start (two terminals)

### 1 — Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API + docs: http://localhost:8000/docs  ·  starts a synthetic feed, so the whole
demo works with **no camera and no heavy deps**.

### 2 — Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 — the dashboard. Vite proxies `/api` → `:8000`, so
there's nothing else to configure.

### Real video path (optional)
Install the AI deps (`opencv-python`, `mediapipe`, `scikit-learn`), download the
res10 model files into `backend/models/` (see its README), then:
```bash
export OBSCURA_VIDEO=/path/to/clip.mp4   # or a webcam index like 0
```
Restart uvicorn and click **Use real feed** in the dashboard's reveal panel.

---

## Run the tests
```bash
cd backend
pip install pytest
pytest -q
```
12 tests cover the DP mechanism + budget, Shamir reconstruction, AES sealing,
the tamper-evident audit chain, and a full API smoke test.

## Deploy (optional)
One command, whole app on one port:
```bash
docker compose up --build      # then open http://localhost:8000
```
Or push to Render / Railway / Fly.io — they build the Dockerfile automatically.
See `DEPLOY.md` for details.

## Quick run (local dev)
- Windows: double-click `run.bat`
- Mac/Linux: `./run.sh`
(Starts backend on 8080 + frontend on 5173. The backend port is set in
`frontend/vite.config.js`.)

## What's real (and tested)
- DP engine: Laplace mean≈0, stdev≈1.41, ε budget decrements, k-anonymity suppresses.
- Shamir 2-of-3 over the 521-bit prime field; any 2 shares reconstruct, 1 cannot.
- AES-GCM seal/unseal; hash-chain audit detects silent edits.
- Privacy Auditor: real ORB re-ID attempts on blurred faces → 0 successes.
- Safety Brain: autoencoder reconstruction-error anomaly detection (+ fallbacks).
- NL assistant: answers count/busy queries, refuses out-of-scope ones.
- React+Vite frontend builds clean; all panels poll the live API.

See `docs/architecture.md` for the full diagram.
