# OBSCURA — submission writeup

Paste/adapt this for Devpost/Unstop. Replace the links at the bottom.

## Inspiration
The hackathon theme — "Mass Surveillance vs Public Safety" — frames a real
dilemma: modern safety systems (CCTV, crowd analytics, facial recognition) work
by collecting identity, which is exactly what erodes privacy. Most solutions pick
a side. We wanted to prove you don't have to.

## What it does
OBSCURA is a public-safety analytics platform that delivers the safety signal
authorities need — crowd density, surges, anomalies — while making individual
identification structurally impossible. It rests on five guarantees:

1. **Anonymize at source** — faces are redacted at the edge before any feature is computed or stored.
2. **Differential privacy** — released statistics carry calibrated Laplace noise, with a per-zone privacy budget that regenerates over time and refuses to over-report; small groups are suppressed (k-anonymity).
3. **Threshold cryptography** — identities are AES-sealed and the key is split via Shamir 2-of-3 across police, an oversight officer, and the judiciary. No single party can de-anonymize anyone.
4. **Tamper-evident audit** — every unlock is appended to a SHA-256 hash chain that anyone can verify; altering the past breaks the chain.
5. **Measured privacy** — an adversarial "Privacy Auditor" continuously attacks our own redacted output trying to re-identify people, and its failure rate is published as a live Privacy Score.

A Safety Brain (autoencoder anomaly detection) flags events from movement, never
identity, and a natural-language assistant can only ever read the
differentially-private aggregate layer.

## How we built it
- **Backend:** Python, FastAPI. Pure-Python differential privacy (Laplace + budget
  + k-anonymity); Shamir secret sharing over a 521-bit prime field; AES-GCM;
  hash-chain audit log; scikit-learn autoencoder; OpenCV face redaction; an ORB
  feature-matcher as the re-identification attacker.
- **Frontend:** React + Vite, a forensic-console UI with a live raw-vs-redacted reveal.
- **Quality:** 12 automated tests (pytest) covering every guarantee; Dockerized for one-command deployment.

## Challenges
Designing accountability that's real, not theatrical — the multi-party unlock and
the tamper-evident ledger — and proving privacy by measuring an attacker's failure
rather than just asserting it.

## What's real vs. demo
All five guarantees are real and tested. The default feed is synthetic (so it runs
anywhere); the real OpenCV camera path is implemented and can be enabled with a
video source and model files. The on-screen "true count" is a demo-only honesty
panel to make the privacy gap visible; it would not exist in production.

## Accomplishments
A working, tested, deployable system that dissolves the surveillance-vs-privacy
trade-off instead of picking a side.

## What's next
On-edge deployment, real pose-based analytics at scale, formal DP accounting
across multiple query types, and a production key-management integration.

## Links
- GitHub: https://github.com/RaktimChandra/obscura
- Demo video: https://drive.google.com/file/d/1n9ycH-6jrDkHfCHeWnuI93_eDsOL4hfi/view?usp=drive_link
- Live demo (optional): https://obscura-tr8o.onrender.com/

## Team VORTEX
Raktim Chandra · Nipun Dewangan · Juhi Hai · Pronov Mazumdar
