# OBSCURA — demo video script (target 2:30)

Record at 1080p with OBS Studio (free) or Windows Game Bar (Win+G). Have both
servers running and the dashboard open at http://localhost:5173 before you start.
Do one full dry run first. Speak slowly; let each visual land.

---

### Shot 1 — The tension (0:00–0:20)
**On screen:** the dashboard, full view.
**Say:** "Cities want safety. Citizens fear surveillance. Today you're forced to
pick one. OBSCURA refuses to choose — it's public-safety monitoring that is
*mathematically incapable* of becoming mass surveillance."

### Shot 2 — The reveal (0:20–1:00)
**Do:** Slowly drag the wipe slider in the Edge Anonymization panel from right to left.
**Say:** "Same camera, one feed. On the left, raw — every face exposed, every
person tagged with an identity. On the right, OBSCURA — faces redacted at the
source, only anonymous skeletons and a head-count remain." Pause on the footer.
"Raw exposes seven identities. OBSCURA exposes zero. Nothing identifying is ever
stored."

### Shot 3 — Privacy you can measure (1:00–1:30)
**Do:** Point to the Analytics panel, then the Privacy Auditor.
**Say:** "The dashboard reports the crowd size — but look: the reported number
never equals the true count. That gap is calibrated differential-privacy noise,
so no single person's presence is detectable. And we don't just claim privacy —
our own AI attacks the redacted feed thousands of times trying to re-identify
people." Point at 100%. "It has never once succeeded."

### Shot 4 — Safety without identity (1:30–1:50)
**Do:** Point to the Safety Brain alert stream.
**Say:** "An anomaly model watches movement and density — it can flag a crowd
surge or a fall — entirely from motion, never from faces."

### Shot 5 — Accountable access (1:50–2:20)
**Do:** Click "Open de-anonymization request." Submit the **police** share (stays
locked). Submit the **judiciary** share (identity reveals). Point to the new red
line in the ledger.
**Say:** "When police genuinely need an identity, no single person can unlock it.
It takes two of three independent key-holders. Watch — one share isn't enough.
Two, and only now, the identity is revealed — and a permanent record is written
to a public, tamper-evident ledger."

### Shot 6 — Tamper proof + close (2:20–2:40)
**Do:** (Optional, pre-arranged second terminal) run `python demo_tamper.py`;
the ledger flips to red TAMPERED.
**Say:** "And if anyone alters that ledger, the chain breaks instantly and
publicly. Safety with a receipt. Surveillance that cannot be abused. That's OBSCURA."

---
**Tips:** keep mouse movements slow and deliberate; do the break-glass step at
least twice in rehearsal so it's smooth; if real video is risky, demo the
simulation and just mention the real camera path exists.
