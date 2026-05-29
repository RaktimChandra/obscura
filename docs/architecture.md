# OBSCURA — architecture

Data flows top to bottom; two guarantees run in parallel.

```
                        Live video feed
                              |
                     Edge anonymization
              (redact faces/plates; extract pose,
               counts, density, motion — no pixels kept)
                       /             \
          anonymous features      sealed identity crop
                  |                        |
        +---------+---------+      AES-GCM seal; key split
        |                   |      via Shamir 2-of-3, key discarded
   Differential        Safety Brain              |
     privacy        (autoencoder anomaly    Accountable break-glass
  (Laplace + budget   detection: surge/      (t-of-n quorum unlock,
   + k-anonymity)     fall/loiter)            every unlock audited)
        |                   |                        |
   Authority dashboard  Threat alerts        Tamper-evident ledger
                                               (public, verifiable)

        Privacy Auditor (red-team): continuously attempts ORB
        re-identification on the redacted output and fails ->
        published as the Privacy Guarantee Score.
```

## Guarantees, in one line each
- **Anonymize at source** — identity is redacted before any feature is computed.
- **Differential privacy** — released counts carry Laplace noise (epsilon budget per zone, k-anonymity suppression) so no individual is detectable.
- **Threshold crypto** — no single party can de-anonymize; 2 of 3 holders required.
- **Tamper-evident audit** — every unlock is hash-chained and publicly verifiable.
- **Measured privacy** — an adversarial model attacks our own output; its failure rate is the score.

## Subsystems → files
- `app/anonymizer/engine.py` — OpenCV redaction, pose, MJPEG; synthetic feed.
- `app/privacy/dp.py` — Laplace mechanism, budget, k-anonymity.
- `app/privacy/auditor.py` — ORB-based adversarial re-identification.
- `app/privacy/assistant.py` — NL questions, answerable only via the DP layer.
- `app/safety/brain.py` — autoencoder anomaly detection (+ fallbacks).
- `app/vault/{shamir,crypto,vault,audit}.py` — threshold unlock + hash chain.
- `frontend/` — React + Vite forensic-console dashboard.
