"""Tamper demo — prove the audit ledger is tamper-evident.

Run this while the backend is running and you have done at least one break-glass
unlock (so there is an interesting entry). It silently edits a past audit
entry's reason directly in the database — exactly what a corrupt insider might
do to hide why a record was opened.

Within ~3 seconds the dashboard's Transparency Ledger flips from green
"CHAIN VERIFIED" to red "TAMPERED", because the entry's stored hash no longer
matches its recomputed hash and every link after it breaks.

Usage:
    python demo_tamper.py            # tamper with the latest entry
    python demo_tamper.py --restore  # delete the db so a restart reseeds clean
"""
import sqlite3
import sys
import os

DB = os.path.join(os.path.dirname(__file__), "obscura.db")


def tamper():
    if not os.path.exists(DB):
        print("No obscura.db yet — start the backend first.")
        return
    c = sqlite3.connect(DB)
    row = c.execute("SELECT seq, action, reason FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
    if not row:
        print("Audit log is empty — trigger a break-glass unlock first.")
        return
    seq, action, reason = row
    c.execute("UPDATE audit SET reason=? WHERE seq=?", ("(quietly altered)", seq))
    c.commit(); c.close()
    print(f"Tampered with entry #{seq} ({action}).")
    print("Old reason:", reason)
    print("Watch the dashboard ledger flip to red TAMPERED within ~3 seconds.")


def restore():
    if os.path.exists(DB):
        os.remove(DB)
        print("Deleted obscura.db. Restart uvicorn to reseed a clean, verified chain.")
    else:
        print("No obscura.db to remove.")


if __name__ == "__main__":
    if "--restore" in sys.argv:
        restore()
    else:
        tamper()
