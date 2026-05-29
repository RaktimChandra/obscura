"""The identity vault and accountable break-glass flow.

seal_identity(): encrypt an identity, split its key into holder shares, store
only the ciphertext. The key is gone — no single party (not even the operator)
can decrypt.

Break-glass: a requester opens a request; key holders submit shares; once t
shares arrive, the key is reconstructed, the record decrypted, and — crucially
— the event is written to the immutable audit log before the plaintext is
returned. Every un-blurring leaves a permanent, public receipt.
"""
from __future__ import annotations

import time
import uuid

from . import crypto, shamir, audit
from .. import store
from ..config import SHAMIR_T, SHAMIR_N, KEY_HOLDERS


def seal_identity(plaintext: str) -> dict:
    """Seal an identity record. Returns the record_id and the per-holder
    shares (in production these are delivered to each holder out-of-band)."""
    record_id = "rec_" + uuid.uuid4().hex[:10]
    key = crypto.generate_key()
    sealed = crypto.seal(plaintext.encode(), key)
    store.put_sealed(record_id, sealed, time.time())

    shares = shamir.split_secret(crypto.key_to_int(key), SHAMIR_T, SHAMIR_N)
    holder_shares = {
        KEY_HOLDERS[i]: shamir.share_to_str(shares[i]) for i in range(SHAMIR_N)
    }
    audit.append("seal", approvers=["system"], record_id=record_id,
                 reason="identity sealed at capture")
    # The key itself is intentionally not returned or stored.
    return {"record_id": record_id, "holder_shares": holder_shares}


def open_request(record_id: str, reason: str, requester: str) -> dict:
    if store.get_sealed(record_id) is None:
        raise KeyError("unknown record")
    request_id = "req_" + uuid.uuid4().hex[:10]
    store.put_breakglass(request_id, record_id, reason, requester, time.time())
    audit.append("breakglass_request", approvers=[requester],
                 record_id=record_id, reason=reason)
    return {"request_id": request_id, "record_id": record_id,
            "status": "pending", "shares_collected": 0, "shares_required": SHAMIR_T}


def submit_share(request_id: str, holder_id: str, share: str) -> dict:
    req = store.get_breakglass(request_id)
    if req is None:
        raise KeyError("unknown request")
    if req["status"] != "pending":
        return _status(req)

    import json
    shares = json.loads(req["shares"])
    # avoid duplicate holders padding the quorum
    if not any(s["holder"] == holder_id for s in shares):
        shares.append({"holder": holder_id, "share": share})

    if len(shares) >= SHAMIR_T:
        revealed = _reconstruct_and_unseal(req["record_id"], shares)
        store.update_breakglass(request_id, shares, "unlocked")
        audit.append(
            "breakglass_unlock",
            approvers=[s["holder"] for s in shares],
            record_id=req["record_id"],
            reason=req["reason"],
        )
        req = store.get_breakglass(request_id)
        out = _status(req)
        out["revealed"] = revealed
        return out

    store.update_breakglass(request_id, shares, "pending")
    return _status(store.get_breakglass(request_id))


def _reconstruct_and_unseal(record_id: str, shares: list) -> str:
    points = [shamir.share_from_str(s["share"]) for s in shares]
    key_int = shamir.reconstruct(points)
    key = crypto.int_to_key(key_int)
    sealed = store.get_sealed(record_id)
    return crypto.unseal(sealed, key).decode()


def _status(req) -> dict:
    import json
    shares = json.loads(req["shares"]) if req["shares"] else []
    return {
        "request_id": req["request_id"],
        "record_id": req["record_id"],
        "status": req["status"],
        "shares_collected": len(shares),
        "shares_required": SHAMIR_T,
        "revealed": None,
    }
