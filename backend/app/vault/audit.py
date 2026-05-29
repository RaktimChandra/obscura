"""Append-only, tamper-evident audit log.

Every entry binds to the previous one: entry_hash = SHA256(canonical(entry) ||
prev_hash). Editing or deleting any past entry changes its hash and breaks
every link after it, so publishing just the head hash lets anyone verify the
whole chain is intact. This is the "surveillance with a receipt" guarantee.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Optional

from .. import store

GENESIS = "0" * 64


def _hash_entry(entry: dict, prev_hash: str) -> str:
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((payload + prev_hash).encode()).hexdigest()


def append(action: str, approvers: list[str] | None = None,
           record_id: Optional[str] = None, reason: Optional[str] = None) -> dict:
    last = store.last_audit()
    prev_hash = last["entry_hash"] if last else GENESIS
    ts = time.time()
    body = {
        "ts": round(ts, 3),
        "action": action,
        "approvers": approvers or [],
        "record_id": record_id,
        "reason": reason,
    }
    entry_hash = _hash_entry(body, prev_hash)
    seq = store.insert_audit(
        ts, action, approvers or [], record_id, reason, prev_hash, entry_hash
    )
    return {"seq": seq, "prev_hash": prev_hash, "entry_hash": entry_hash, **body}


def head() -> dict:
    last = store.last_audit()
    if not last:
        return {"seq": 0, "head_hash": GENESIS, "verified": True}
    return {"seq": last["seq"], "head_hash": last["entry_hash"],
            "verified": verify_chain()}


def verify_chain() -> bool:
    """Recompute the entire chain and confirm no link was altered."""
    prev_hash = GENESIS
    for row in store.all_audit():
        body = {
            "ts": round(row["ts"], 3),
            "action": row["action"],
            "approvers": json.loads(row["approvers"]),
            "record_id": row["record_id"],
            "reason": row["reason"],
        }
        expected = _hash_entry(body, prev_hash)
        if expected != row["entry_hash"] or row["prev_hash"] != prev_hash:
            return False
        prev_hash = row["entry_hash"]
    return True


def entries() -> list[dict]:
    out = []
    for row in store.all_audit():
        out.append({
            "seq": row["seq"], "ts": row["ts"], "action": row["action"],
            "approvers": json.loads(row["approvers"]), "record_id": row["record_id"],
            "reason": row["reason"], "prev_hash": row["prev_hash"],
            "entry_hash": row["entry_hash"],
        })
    return out
