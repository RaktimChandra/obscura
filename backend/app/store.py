"""SQLite persistence for OBSCURA.

Keeps three tables: sealed identity records, the append-only audit chain, and
in-flight break-glass requests. Deliberately tiny — this is a hackathon demo,
not a production datastore.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Optional

from .config import DB_PATH

_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _lock, _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS sealed_records (
                record_id TEXT PRIMARY KEY,
                nonce TEXT, ciphertext TEXT, tag TEXT,
                created_ts REAL
            );
            CREATE TABLE IF NOT EXISTS audit (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL, action TEXT, approvers TEXT,
                record_id TEXT, reason TEXT,
                prev_hash TEXT, entry_hash TEXT
            );
            CREATE TABLE IF NOT EXISTS breakglass (
                request_id TEXT PRIMARY KEY,
                record_id TEXT, reason TEXT, requester TEXT,
                shares TEXT, status TEXT, created_ts REAL
            );
            """
        )


# ---------- sealed records ----------
def put_sealed(record_id: str, sealed: dict, ts: float) -> None:
    with _lock, _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO sealed_records VALUES (?,?,?,?,?)",
            (record_id, sealed["nonce"], sealed["ciphertext"], sealed["tag"], ts),
        )


def get_sealed(record_id: str) -> Optional[dict]:
    with _lock, _conn() as c:
        row = c.execute(
            "SELECT * FROM sealed_records WHERE record_id=?", (record_id,)
        ).fetchone()
    if not row:
        return None
    return {"nonce": row["nonce"], "ciphertext": row["ciphertext"], "tag": row["tag"]}


# ---------- audit ----------
def last_audit() -> Optional[sqlite3.Row]:
    with _lock, _conn() as c:
        return c.execute(
            "SELECT * FROM audit ORDER BY seq DESC LIMIT 1"
        ).fetchone()


def insert_audit(ts, action, approvers, record_id, reason, prev_hash, entry_hash) -> int:
    with _lock, _conn() as c:
        cur = c.execute(
            "INSERT INTO audit (ts,action,approvers,record_id,reason,prev_hash,entry_hash)"
            " VALUES (?,?,?,?,?,?,?)",
            (ts, action, json.dumps(approvers), record_id, reason, prev_hash, entry_hash),
        )
        return cur.lastrowid


def all_audit() -> list[sqlite3.Row]:
    with _lock, _conn() as c:
        return c.execute("SELECT * FROM audit ORDER BY seq ASC").fetchall()


# ---------- break-glass ----------
def put_breakglass(request_id, record_id, reason, requester, ts) -> None:
    with _lock, _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO breakglass VALUES (?,?,?,?,?,?,?)",
            (request_id, record_id, reason, requester, json.dumps([]), "pending", ts),
        )


def get_breakglass(request_id: str) -> Optional[sqlite3.Row]:
    with _lock, _conn() as c:
        return c.execute(
            "SELECT * FROM breakglass WHERE request_id=?", (request_id,)
        ).fetchone()


def update_breakglass(request_id: str, shares: list, status: str) -> None:
    with _lock, _conn() as c:
        c.execute(
            "UPDATE breakglass SET shares=?, status=? WHERE request_id=?",
            (json.dumps(shares), status, request_id),
        )
